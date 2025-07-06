from sqlalchemy.orm import Session
from datetime import date
from domain.care import care_model

def create_care_log(db: Session, owner_id: int):
    db_log = db.query(care_model.CareLog).filter(
        care_model.CareLog.owner_id == owner_id,
        care_model.CareLog.completion_date == date.today(),
    ).first()

    if db_log:
        return db_log

    db_log = care_model.CareLog(
        completion_date = date.today(),
        owner_id = owner_id,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_care_logs_for_week(db: Session, owner_id: int, start_of_week: date, end_of_week: date):
    return db.query(care_model.CareLog).filter(
        care_model.CareLog.owner_id == owner_id,
        care_model.CareLog.completion_date >= start_of_week,
        care_model.CareLog.completion_date <= end_of_week,
    ).all()