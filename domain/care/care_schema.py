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