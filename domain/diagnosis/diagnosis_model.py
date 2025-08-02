from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.session import Base

class DiagnosisLog(Base):
    __tablename__ = "diagnosis_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), nullable=False, index=True)  # 진단 세션 ID
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    diagnosis_date = Column(Date, nullable=False, index=True)
    
    # 진단 점수
    total_score = Column(Float, nullable=False)
    language_score = Column(Float, nullable=False)
    acoustic_score = Column(Float, nullable=False)
    check_score = Column(Float, nullable=False)
    
    # 진단 결과
    dementia_result = Column(Integer, nullable=False)  # 0: 정상, 1: 치매
    risk_level = Column(String(20), nullable=False)  # normal, mild, severe
    threshold = Column(Integer, nullable=False)
    
    # 상세 분석
    detailed_analysis = Column(Text, nullable=True)
    
    # 사용자 정보 (진단 시점)
    user_age = Column(Integer, nullable=False)
    user_education = Column(String(50), nullable=False)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    # 관계 설정
    user = relationship("User", back_populates="diagnosis_logs") 