from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class DiagnosisLogCreate(BaseModel):
    session_id: str
    user_id: int
    diagnosis_date: date
    total_score: float
    language_score: float
    acoustic_score: float
    check_score: float
    dementia_result: int
    risk_level: str
    threshold: int
    detailed_analysis: Optional[str] = None

class DiagnosisLog(DiagnosisLogCreate):
    id: int
    user_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DiagnosisHistoryResponse(BaseModel):
    id: int
    session_id: str
    diagnosis_date: date
    total_score: float
    dementia_result: int
    risk_level: str
    created_at: datetime
    
    class Config:
        from_attributes = True 