from sqlalchemy.orm import Session
from .care_model import CareLog
from .care_schema import CareLogCreate
from datetime import date

def create_care_log(db: Session, care_log: CareLogCreate):
    db_log = CareLog(
        user_id=care_log.user_id,
        text=care_log.text,
        completion_date=care_log.completion_date
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
        CareLog.completion_date >= start_of_week,
        CareLog.completion_date <= end_of_week
    ).order_by(CareLog.completion_date).all()