from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ReportLogBase(BaseModel):
    user_id: int
    report_type: str  # 'diagnosis' or 'care'
    report_data: Dict[str, Any]

class ReportLogCreate(ReportLogBase):
    pass

class ReportLog(ReportLogBase):
    id: int
    generated_at: datetime
    sent_at: Optional[datetime] = None
    email_sent: bool = False

    class Config:
        from_attributes = True

class DiagnosisReportRequest(BaseModel):
    user_id: int
    acoustic_score_vit: float
    acoustic_score_lgbm: float
    language_score_BERT: float
    language_score_gpt: float
    user_email: str
    user_name: str

class CareReportRequest(BaseModel):
    user_id: int
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    user_email: str
    user_name: str
    weekly_conversations: Optional[List[Dict[str, Any]]] = None  # 백엔드에서 자동으로 채움

class EmailReportRequest(BaseModel):
    to_email: str
    subject: str
    html_content: str
    report_type: str
    user_id: int

class ReportResponse(BaseModel):
    message: str
    report_id: Optional[int] = None
    sent_at: Optional[str] = None
