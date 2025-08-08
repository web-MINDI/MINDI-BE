from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.session import Base

class CareLog(Base):
    __tablename__ = "care_logs"
    id = Column(Integer, primary_key=True, index=True)
    conversation_date = Column(Date, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user_question = Column(String(2048), nullable=False)  # 사용자 질문
    ai_reply = Column(String(4096), nullable=False)      # AI 답변
    conversation_id = Column(String(36), nullable=False, index=True)  # 대화 세션 ID
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="care_logs")