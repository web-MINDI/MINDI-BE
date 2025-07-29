from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

class CareLogBase(BaseModel):
    user_id: int
    user_question: str      # 사용자 질문
    ai_reply: str          # AI 답변
    conversation_date: date
    conversation_id: str   # 대화 세션 ID

class CareLogCreate(CareLogBase):
    pass

class CareLogRead(CareLogBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class CareLog(CareLogRead):
    pass

class PersonalizedGreetingResponse(BaseModel):
    """개인화된 인사말 응답"""
    greeting_text: str
    has_previous_conversation: bool
    
class DailyStatusResponse(BaseModel):
    """일일 기록 현황 응답"""
    date: date
    has_conversation: bool
    conversation_count: int
    last_conversation_time: Optional[datetime] = None

class WeeklyStatusResponse(BaseModel):
    """주간 기록 현황 응답"""
    week_start: date
    week_end: date
    daily_status: List[dict]  # 7일간 일별 상태
    total_conversations: int
    completed_days: int
    completion_rate: float  # 완료율 (0.0 ~ 1.0)

class ConversationSummaryResponse(BaseModel):
    """대화 요약 응답"""
    date: date
    summary_text: str
    total_conversations: int
    key_topics: List[str]
    emotional_tone: Optional[str] = None
    duration_minutes: Optional[int] = None

class PreviousConversationContext(BaseModel):
    """가장 최근 대화한 날의 컨텍스트 (AI 서버 전송용)"""
    user_id: int
    recent_conversations: List[dict]