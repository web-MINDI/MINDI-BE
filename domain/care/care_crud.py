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

def get_total_conversation_count(db: Session, user_id: int) -> int:
    """사용자의 총 대화 횟수 반환"""
    return db.query(CareLog).filter(
        CareLog.user_id == user_id
    ).count()

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

def get_weekly_status(db: Session, user_id: int, target_date: Optional[date] = None) -> dict:
    """주간 기록 현황 조회 (월요일부터 일요일까지)"""
    if target_date is None:
        target_date = date.today()
    
    # 해당 주의 월요일과 일요일 계산
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)  # 월요일
    week_end = week_start + timedelta(days=6)  # 일요일
    
    # 주간 대화 로그 조회
    weekly_logs = get_care_logs_for_week(db, user_id, week_start, week_end)
    
    # 일별 상태 생성 (월요일부터 일요일까지)
    daily_status = []
    total_conversations = 0
    completed_days = 0
    
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        day_logs = [log for log in weekly_logs if log.conversation_date == current_date]
        
        has_conversation = len(day_logs) > 0
        conversation_count = len(day_logs)
        last_conversation_time = day_logs[-1].created_at if day_logs else None
        
        if has_conversation:
            completed_days += 1
            total_conversations += conversation_count
        
        daily_status.append({
            "date": current_date,
            "day_of_week": ["월", "화", "수", "목", "금", "토", "일"][i],
            "has_conversation": has_conversation,
            "conversation_count": conversation_count,
            "last_conversation_time": last_conversation_time
        })
    
    # 완료율 계산
    completion_rate = completed_days / 7.0 if completed_days > 0 else 0.0
    
    return {
        "week_start": week_start,
        "week_end": week_end,
        "daily_status": daily_status,
        "total_conversations": total_conversations,
        "completed_days": completed_days,
        "completion_rate": completion_rate
    }

def get_previous_day_conversations(db: Session, user_id: int, target_date: Optional[date] = None) -> List[CareLog]:
    """전날 대화 조회 (키워드 추출용)"""
    if target_date is None:
        target_date = date.today()
    
    previous_date = target_date - timedelta(days=1)
    return get_daily_conversations(db, user_id, previous_date)