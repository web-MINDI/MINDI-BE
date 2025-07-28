from sqlalchemy.orm import Session
from .care_model import CareLog
from .care_schema import CareLogCreate
from datetime import date
from typing import List

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