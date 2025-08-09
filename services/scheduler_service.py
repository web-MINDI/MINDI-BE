import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import List, Optional
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.session import get_db
from domain.user import user_crud, user_schema
from domain.report import report_crud, report_schema
from domain.care import care_crud
from services.email_service import email_service
import httpx

logger = logging.getLogger(__name__)

class SchedulerService:
    """스케줄링 서비스 클래스"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.ai_server_url = "http://localhost:8001"
        
    def start(self):
        """스케줄러 시작"""
        try:
            # 주간 케어 리포트 자동 생성 (매주 일요일 오전 9시)
            self.scheduler.add_job(
                func=self.generate_weekly_care_reports,
                trigger=CronTrigger(day_of_week='sun', hour=9, minute=0),
                id='weekly_care_reports',
                name='주간 케어 리포트 생성',
                replace_existing=True
            )
            
            # 스케줄러 시작
            self.scheduler.start()
            logger.info("스케줄러가 성공적으로 시작되었습니다.")
            
        except Exception as e:
            logger.error(f"스케줄러 시작 실패: {e}")
    
    def stop(self):
        """스케줄러 중지"""
        try:
            self.scheduler.shutdown()
            logger.info("스케줄러가 중지되었습니다.")
        except Exception as e:
            logger.error(f"스케줄러 중지 실패: {e}")
    
    async def generate_weekly_care_reports(self):
        """주간 케어 리포트 자동 생성 및 이메일 발송"""
        logger.info("주간 케어 리포트 생성 작업 시작")
        
        try:
            # 데이터베이스 세션 생성
            db = next(get_db())
            
            # 유료 구독자 목록 조회
            premium_users = self._get_premium_users(db)
            
            if not premium_users:
                logger.info("유료 구독자가 없습니다.")
                return
            
            # 분석 기간 설정 (지난 주 월요일 ~ 일요일)
            end_date = date.today() - timedelta(days=date.today().weekday() + 1)  # 지난 주 일요일
            start_date = end_date - timedelta(days=6)  # 지난 주 월요일
            
            logger.info(f"분석 기간: {start_date} ~ {end_date}")
            
            # 각 유료 구독자에 대해 리포트 생성
            success_count = 0
            error_count = 0
            
            for user in premium_users:
                try:
                    await self._generate_user_care_report(
                        db, user, start_date, end_date
                    )
                    success_count += 1
                    logger.info(f"사용자 {user.id} ({user.name}) 리포트 생성 성공")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"사용자 {user.id} ({user.name}) 리포트 생성 실패: {e}")
            
            logger.info(f"주간 케어 리포트 생성 완료: 성공 {success_count}건, 실패 {error_count}건")
            
        except Exception as e:
            logger.error(f"주간 케어 리포트 생성 작업 실패: {e}")
        finally:
            db.close()
    
    def _get_premium_users(self, db: Session) -> List[user_schema.User]:
        """유료 구독자 목록 조회"""
        try:
            # subscription_type이 'premium' 또는 'premium_plus'인 사용자 조회
            users = user_crud.get_users_by_subscription_type(db, ['premium', 'premium_plus'])
            return [user for user in users if user.email]  # 이메일이 있는 사용자만
        except Exception as e:
            logger.error(f"유료 구독자 조회 실패: {e}")
            return []
    
    async def _generate_user_care_report(
        self,
        db: Session,
        user: user_schema.User,
        start_date: date,
        end_date: date
    ):
        """개별 사용자의 케어 리포트 생성 및 이메일 발송"""
        
        # 주간 대화 데이터 수집
        weekly_conversations = []
        current_date = start_date
        
        while current_date <= end_date:
            # 해당 날짜의 대화 로그 조회
            daily_logs = care_crud.get_daily_conversations(db, user.id, current_date)
            
            # 대화 데이터 구성
            conversations = []
            for log in daily_logs:
                conversations.append({
                    "user_question": log.user_question,
                    "ai_reply": log.ai_reply,
                    "conversation_id": log.conversation_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })
            
            weekly_conversations.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "conversations": conversations
            })
            
            current_date += timedelta(days=1)
        
        # AI 서버에 케어 리포트 생성 요청
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_server_url}/generate-care-report",
                    json={
                        "user_id": user.id,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "user_email": user.email,
                        "user_name": user.name,
                        "weekly_conversations": weekly_conversations
                    },
                    timeout=60
                )
                
                if response.status_code != 200:
                    raise Exception(f"AI 서버 응답 오류: {response.status_code}")
                
                ai_response = response.json()
                
                # 리포트 데이터를 DB에 저장
                report_data = {
                    "report_html": ai_response["report_html"],
                    "report_text": ai_response["report_text"],
                    "weekly_data": ai_response["weekly_data"],
                    "overall_comment": ai_response["overall_comment"],
                    "care_recommendations": ai_response["care_recommendations"],
                    "period": {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    },
                    "conversation_count": sum(len(day["conversations"]) for day in weekly_conversations)
                }
                
                report_log = report_crud.create_report_log(
                    db,
                    report_schema.ReportLogCreate(
                        user_id=user.id,
                        report_type="care",
                        report_data=report_data
                    )
                )
                
                # 이메일 발송
                if user.email:
                    email_success = email_service.send_care_report(
                        to_email=user.email,
                        user_name=user.name,
                        report_html=ai_response["report_html"],
                        report_text=ai_response["report_text"],
                        period={
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d")
                        },
                        conversation_count=sum(len(day["conversations"]) for day in weekly_conversations)
                    )
                    
                    if email_success:
                        # 이메일 발송 상태 업데이트
                        report_crud.update_report_sent_status(db, report_log.id, datetime.now())
                        logger.info(f"사용자 {user.id} ({user.name}) 이메일 발송 성공")
                    else:
                        logger.error(f"사용자 {user.id} ({user.name}) 이메일 발송 실패")
                
        except Exception as e:
            logger.error(f"사용자 {user.id} 리포트 생성 실패: {e}")
            raise
    
    async def generate_manual_weekly_report(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> bool:
        """수동으로 주간 케어 리포트 생성 (테스트용)"""
        try:
            db = next(get_db())
            user = user_crud.get_user_by_id(db, user_id)
            
            if not user:
                logger.error(f"사용자를 찾을 수 없습니다: {user_id}")
                return False
            
            await self._generate_user_care_report(db, user, start_date, end_date)
            return True
            
        except Exception as e:
            logger.error(f"수동 리포트 생성 실패: {e}")
            return False
        finally:
            db.close()

# 전역 스케줄러 인스턴스
scheduler_service = SchedulerService()
