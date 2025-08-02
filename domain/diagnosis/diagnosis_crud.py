from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, datetime, timezone
from typing import List, Optional

from . import diagnosis_model
from . import diagnosis_schema

def create_diagnosis_log(db: Session, diagnosis_log: diagnosis_schema.DiagnosisLogCreate) -> diagnosis_model.DiagnosisLog:
    """진단 결과를 데이터베이스에 저장"""
    # 현재 시간을 명시적으로 설정
    current_time = datetime.now(timezone.utc)
    
    db_diagnosis_log = diagnosis_model.DiagnosisLog(
        **diagnosis_log.model_dump(),
        created_at=current_time
    )
    db.add(db_diagnosis_log)
    db.commit()
    db.refresh(db_diagnosis_log)
    return db_diagnosis_log

def get_diagnosis_log_by_id(db: Session, diagnosis_id: int) -> Optional[diagnosis_model.DiagnosisLog]:
    """ID로 진단 결과 조회"""
    return db.query(diagnosis_model.DiagnosisLog).filter(diagnosis_model.DiagnosisLog.id == diagnosis_id).first()

def get_diagnosis_log_by_session_id(db: Session, session_id: str) -> Optional[diagnosis_model.DiagnosisLog]:
    """세션 ID로 진단 결과 조회"""
    return db.query(diagnosis_model.DiagnosisLog).filter(diagnosis_model.DiagnosisLog.session_id == session_id).first()

def get_latest_diagnosis_by_user(db: Session, user_id: int) -> Optional[diagnosis_model.DiagnosisLog]:
    """사용자의 최신 진단 결과 조회"""
    return db.query(diagnosis_model.DiagnosisLog)\
        .filter(diagnosis_model.DiagnosisLog.user_id == user_id)\
        .order_by(desc(diagnosis_model.DiagnosisLog.created_at))\
        .first()

def get_diagnosis_history_by_user(db: Session, user_id: int, limit: int = 10) -> List[diagnosis_model.DiagnosisLog]:
    """사용자의 진단 기록 조회 (최신순)"""
    return db.query(diagnosis_model.DiagnosisLog)\
        .filter(diagnosis_model.DiagnosisLog.user_id == user_id)\
        .order_by(desc(diagnosis_model.DiagnosisLog.created_at))\
        .limit(limit)\
        .all()

def get_diagnosis_by_date_range(db: Session, user_id: int, start_date: date, end_date: date) -> List[diagnosis_model.DiagnosisLog]:
    """특정 기간의 진단 기록 조회"""
    return db.query(diagnosis_model.DiagnosisLog)\
        .filter(
            diagnosis_model.DiagnosisLog.user_id == user_id,
            diagnosis_model.DiagnosisLog.diagnosis_date >= start_date,
            diagnosis_model.DiagnosisLog.diagnosis_date <= end_date
        )\
        .order_by(desc(diagnosis_model.DiagnosisLog.created_at))\
        .all()

def get_diagnosis_statistics_by_user(db: Session, user_id: int) -> dict:
    """사용자의 진단 통계 정보 조회"""
    diagnosis_logs = db.query(diagnosis_model.DiagnosisLog)\
        .filter(diagnosis_model.DiagnosisLog.user_id == user_id)\
        .all()
    
    if not diagnosis_logs:
        return {
            "total_diagnoses": 0,
            "average_score": 0,
            "dementia_count": 0,
            "normal_count": 0,
            "latest_diagnosis_date": None
        }
    
    total_diagnoses = len(diagnosis_logs)
    average_score = sum(log.total_score for log in diagnosis_logs) / total_diagnoses
    dementia_count = sum(1 for log in diagnosis_logs if log.dementia_result == 1)
    normal_count = total_diagnoses - dementia_count
    latest_diagnosis_date = max(log.diagnosis_date for log in diagnosis_logs)
    
    return {
        "total_diagnoses": total_diagnoses,
        "average_score": round(average_score, 2),
        "dementia_count": dementia_count,
        "normal_count": normal_count,
        "latest_diagnosis_date": latest_diagnosis_date
    } 