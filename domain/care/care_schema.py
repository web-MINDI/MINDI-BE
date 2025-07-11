from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class CareLogBase(BaseModel):
    user_id: int
    text: str
    completion_date: date

class CareLogCreate(CareLogBase):
    pass

class CareLogRead(CareLogBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class CareLog(CareLogRead):
    pass