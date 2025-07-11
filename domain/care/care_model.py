from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.session import Base

class CareLog(Base):
    __tablename__ = "care_logs"
    id = Column(Integer, primary_key=True, index=True)
    completion_date = Column(Date, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="care_logs")