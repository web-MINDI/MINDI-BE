from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship

from database.session import Base

class CareLog(Base):
    __tablename__ = "care_logs"

    id = Column(Integer, primary_key=True, index=True)
    completion_date = Column(Date, nullable=False, index=True)

    owner_id = Column(Integer, ForeignKey("user.id"))
    owner = relationship("User", back_populates="care_logs")