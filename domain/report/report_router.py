from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import httpx
from datetime import datetime, date
from typing import List

from config import settings
from domain.report import report_schema, report_crud
from domain.user import user_schema, user_crud
from database.session import get_db
from security import get_current_user
from services.email_service import email_service
from services.scheduler_service import scheduler_service

router = APIRouter(
    prefix="/report",
    tags=["Report"]
)

AI_REPORT_URL = "http://localhost:8001"

@router.post("/generate-care", response_model=report_schema.ReportResponse)
async def generate_care_report(
    request: report_schema.CareReportRequest,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """케어 대화 데이터를 바탕으로 주간 리포트 생성"""
    try:
        from datetime import datetime, timedelta
        from domain.care import care_crud
        
        # 주간 대화 데이터 수집
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
        
        weekly_conversations = []
        
        # 각 날짜별 대화 데이터 수집
        current_date = start_date
        while current_date <= end_date:
            # 해당 날짜의 대화 로그 조회
            daily_logs = care_crud.get_daily_conversations(
                db, current_user.id, current_date
            )
            
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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_REPORT_URL}/generate-care-report",
                json={
                    "user_id": request.user_id,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "user_email": request.user_email,
                    "user_name": request.user_name,
                    "weekly_conversations": weekly_conversations
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI 서버에서 리포트 생성 실패")
            
            ai_response = response.json()
            
            # 리포트 데이터를 DB에 저장
            report_data = {
                "report_html": ai_response["report_html"],
                "report_text": ai_response["report_text"],
                "weekly_data": ai_response["weekly_data"],
                "overall_comment": ai_response["overall_comment"],
                "care_recommendations": ai_response["care_recommendations"],
                "period": {
                    "start_date": request.start_date,
                    "end_date": request.end_date
                },
                "conversation_count": sum(len(day["conversations"]) for day in weekly_conversations)
            }
            
            report_log = report_crud.create_report_log(
                db,
                report_schema.ReportLogCreate(
                    user_id=current_user.id,
                    report_type="care",
                    report_data=report_data
                )
            )
            
            return report_schema.ReportResponse(
                message="케어 리포트가 성공적으로 생성되었습니다.",
                report_id=report_log.id
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"케어 리포트 생성 실패: {str(e)}")

@router.post("/send-email", response_model=report_schema.ReportResponse)
async def send_report_email(
    request: report_schema.EmailReportRequest,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """리포트 이메일 발송"""
    try:
        # 리포트 타입에 따라 적절한 이메일 발송
        success = False
        
        if request.report_type == "diagnosis":
            # 진단 리포트 이메일 발송
            success = email_service.send_email(
                to_email=request.to_email,
                subject=request.subject,
                html_content=request.html_content
            )
        elif request.report_type == "care":
            # 케어 리포트 이메일 발송
            success = email_service.send_email(
                to_email=request.to_email,
                subject=request.subject,
                html_content=request.html_content
            )
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 리포트 타입입니다.")
        
        if success:
            # 발송 상태 업데이트
            report_crud.update_report_sent_status(db, request.user_id, datetime.now())
            
            return report_schema.ReportResponse(
                message="이메일이 성공적으로 발송되었습니다.",
                sent_at=datetime.now().isoformat()
            )
        else:
            raise HTTPException(status_code=500, detail="이메일 발송에 실패했습니다.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이메일 발송 실패: {str(e)}")

@router.get("/history", response_model=List[report_schema.ReportLog])
async def get_report_history(
    report_type: str = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """사용자의 리포트 이력 조회"""
    try:
        if report_type:
            reports = report_crud.get_recent_reports_by_type(
                db, current_user.id, report_type, days=30
            )
        else:
            reports = report_crud.get_report_logs_by_user(
                db, current_user.id, skip=skip, limit=limit
            )
        
        return reports
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 이력 조회 실패: {str(e)}")

@router.get("/{report_id}", response_model=report_schema.ReportLog)
async def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """특정 리포트 상세 조회"""
    try:
        report = report_crud.get_report_log_by_id(db, report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
        
        if report.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 상세 조회 실패: {str(e)}")

@router.post("/scheduler/start")
async def start_scheduler(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """스케줄러 시작 (관리자용)"""
    try:
        # 관리자 권한 확인 (임시로 모든 사용자 허용)
        scheduler_service.start()
        return {"message": "스케줄러가 성공적으로 시작되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄러 시작 실패: {str(e)}")

@router.post("/scheduler/stop")
async def stop_scheduler(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """스케줄러 중지 (관리자용)"""
    try:
        scheduler_service.stop()
        return {"message": "스케줄러가 중지되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄러 중지 실패: {str(e)}")

@router.post("/scheduler/generate-weekly")
async def generate_weekly_report_manual(
    user_id: int = Body(...),
    start_date: str = Body(...),  # YYYY-MM-DD
    end_date: str = Body(...),    # YYYY-MM-DD
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """수동으로 주간 케어 리포트 생성 (테스트용)"""
    try:
        # 날짜 파싱
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # 스케줄러를 통한 수동 리포트 생성
        success = await scheduler_service.generate_manual_weekly_report(
            user_id, start, end
        )
        
        if success:
            return {"message": "주간 케어 리포트가 성공적으로 생성되었습니다."}
        else:
            raise HTTPException(status_code=500, detail="리포트 생성에 실패했습니다.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수동 리포트 생성 실패: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """스케줄러 상태 조회"""
    try:
        is_running = scheduler_service.scheduler.running
        jobs = scheduler_service.scheduler.get_jobs()
        
        return {
            "is_running": is_running,
            "job_count": len(jobs),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄러 상태 조회 실패: {str(e)}")
