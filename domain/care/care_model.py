from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
    Float,
    Text,
    UniqueConstraint,
)
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


class CareDailyScore(Base):
    __tablename__ = "care_daily_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # 4가지 모델 점수 (0~100 가정)
    acoustic_vit = Column(Integer, nullable=False)
    acoustic_lgbm = Column(Integer, nullable=False)
    language_bert = Column(Integer, nullable=False)
    language_gpt = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # User <-> DailyScore 관계 (User 쪽 변경 없이 backref 사용)
    user = relationship("User", backref="care_daily_scores")

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_care_daily_scores_user_date"),
    )


class CareWeeklyReport(Base):
    __tablename__ = "care_weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)

    week_start = Column(Date, nullable=False, index=True)
    week_end = Column(Date, nullable=False, index=True)

    # 주간 집계된 평균 점수 (실수형)
    avg_acoustic_vit = Column(Float, nullable=True)
    avg_acoustic_lgbm = Column(Float, nullable=True)
    avg_language_bert = Column(Float, nullable=True)
    avg_language_gpt = Column(Float, nullable=True)

    # 리포트 본문 (텍스트/HTML)
    report_text = Column(Text, nullable=True)

    # 이메일 전송 메타데이터
    email_to = Column(String(255), nullable=True)
    email_status = Column(String(50), nullable=True)  # sent, failed, pending 등
    sent_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # User <-> WeeklyReport 관계 (User 쪽 변경 없이 backref 사용)
    user = relationship("User", backref="care_weekly_reports")

    __table_args__ = (
        UniqueConstraint("user_id", "week_start", "week_end", name="uq_care_weekly_reports_user_week"),
    )