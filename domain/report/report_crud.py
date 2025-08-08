from sqlalchemy.orm import Session
from datetime import datetime
from . import report_model, report_schema

def create_report_log(db: Session, report_log: report_schema.ReportLogCreate):
    db_report_log = report_model.ReportLog(
        user_id=report_log.user_id,
        report_type=report_log.report_type,
        report_data=report_log.report_data
    )
    db.add(db_report_log)
    db.commit()
    db.refresh(db_report_log)
    return db_report_log

def get_report_logs_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(report_model.ReportLog).filter(
        report_model.ReportLog.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_report_log_by_id(db: Session, report_id: int):
    return db.query(report_model.ReportLog).filter(
        report_model.ReportLog.id == report_id
    ).first()

def update_report_sent_status(db: Session, report_id: int, sent_at: datetime = None):
    db_report_log = get_report_log_by_id(db, report_id)
    if db_report_log:
        db_report_log.email_sent = True
        if sent_at:
            db_report_log.sent_at = sent_at
        db.commit()
        db.refresh(db_report_log)
    return db_report_log

def get_recent_reports_by_type(db: Session, user_id: int, report_type: str, days: int = 7):
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    return db.query(report_model.ReportLog).filter(
        report_model.ReportLog.user_id == user_id,
        report_model.ReportLog.report_type == report_type,
        report_model.ReportLog.generated_at >= cutoff_date
    ).order_by(report_model.ReportLog.generated_at.desc()).all()
