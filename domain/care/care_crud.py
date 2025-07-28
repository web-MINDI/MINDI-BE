from sqlalchemy.orm import Session
from .care_model import CareLog
from .care_schema import CareLogCreate
from datetime import date, timedelta
from typing import List, Optional

def create_care_log(db: Session, care_log: CareLogCreate):
    db_log = CareLog(
        user_id=care_log.user_id,
        user_question=care_log.user_question,
        ai_reply=care_log.ai_reply,
        conversation_date=care_log.conversation_date,
        conversation_id=care_log.conversation_id
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_last_care_log_by_user(db: Session, user_id: int):
    return db.query(CareLog).filter(CareLog.user_id == user_id).order_by(CareLog.created_at.desc()).first()

def get_care_logs_for_week(db: Session, user_id: int, start_of_week: date, end_of_week: date):
    return db.query(CareLog).filter(
        CareLog.user_id == user_id,
        CareLog.conversation_date >= start_of_week,
        CareLog.conversation_date <= end_of_week
    ).order_by(CareLog.conversation_date).all()

def get_care_logs_by_conversation_id(db: Session, conversation_id: str):
    """특정 대화 세션의 모든 로그 조회"""
    return db.query(CareLog).filter(
        CareLog.conversation_id == conversation_id
    ).order_by(CareLog.created_at).all()

def get_recent_care_logs(db: Session, user_id: int, limit: int = 5):
    """사용자의 최근 대화 로그 조회"""
    return db.query(CareLog).filter(
        CareLog.user_id == user_id
    ).order_by(CareLog.created_at.desc()).limit(limit).all()

def get_conversation_summary(db: Session, conversation_id: str):
    """대화 세션 요약 정보 조회"""
    logs = get_care_logs_by_conversation_id(db, conversation_id)
    if not logs:
        return None
    
    return {
        "conversation_id": conversation_id,
        "start_time": logs[0].created_at,
        "end_time": logs[-1].created_at,
        "turn_count": len(logs),
        "total_duration": (logs[-1].created_at - logs[0].created_at).total_seconds()
    }

def get_latest_care_log_by_conversation(db: Session, conversation_id: str):
    """특정 대화 세션의 최신 로그 조회"""
    return db.query(CareLog).filter(
        CareLog.conversation_id == conversation_id
    ).order_by(CareLog.created_at.desc()).first()

def get_latest_conversation_date_logs(db: Session, user_id: int) -> List[CareLog]:
    """가장 최근에 대화한 날의 모든 대화 조회 (인사말 개인화용)"""
    # 먼저 가장 최근 대화 로그를 찾아서 날짜 확인
    latest_log = db.query(CareLog).filter(
        CareLog.user_id == user_id
    ).order_by(CareLog.created_at.desc()).first()
    
    if not latest_log:
        return []
    
    # 가장 최근 대화 날짜의 모든 대화 조회
    latest_date = latest_log.conversation_date
    return db.query(CareLog).filter(
        CareLog.user_id == user_id,
        CareLog.conversation_date == latest_date
    ).order_by(CareLog.created_at).all()

def get_daily_conversations(db: Session, user_id: int, target_date: Optional[date] = None) -> List[CareLog]:
    """특정 날짜의 모든 대화 조회 (요약용)"""
    if target_date is None:
        target_date = date.today()
    
    return db.query(CareLog).filter(
        CareLog.user_id == user_id,
        CareLog.conversation_date == target_date
    ).order_by(CareLog.created_at).all()

def check_daily_conversation_status(db: Session, user_id: int, target_date: Optional[date] = None) -> bool:
    """특정 날짜에 대화했는지 확인 (일일 기록 현황용)"""
    if target_date is None:
        target_date = date.today()
    
    conversation_count = db.query(CareLog).filter(
        CareLog.user_id == user_id,
        CareLog.conversation_date == target_date
    ).count()
    
    return conversation_count > 0

def get_conversation_categories_from_previous_day(db: Session, user_id: int, target_date: Optional[date] = None) -> List[str]:
    """전날 대화에서 주요 카테고리/키워드 추출 (기본 구현)"""
    previous_conversations = get_previous_day_conversations(db, user_id, target_date)
    
    if not previous_conversations:
        return []
    
    # 간단한 키워드 추출 (실제로는 AI 서버에서 더 정교하게 분석)
    categories = []
    for log in previous_conversations:
        # AI 답변에서 주요 주제 추출 (예시)
        ai_reply = log.ai_reply.lower()
        if any(keyword in ai_reply for keyword in ['가족', '어머니', '아버지', '부모']):
            categories.append('family')
        if any(keyword in ai_reply for keyword in ['음식', '요리', '식사', '밥']):
            categories.append('food')
        if any(keyword in ai_reply for keyword in ['취미', '운동', '산책', '독서']):
            categories.append('hobby')
        if any(keyword in ai_reply for keyword in ['친구', '사람', '만나']):
            categories.append('social')
    
    return list(set(categories))  # 중복 제거