from pydantic import BaseModel
import datetime

class CareLogBase(BaseModel):
    completion_date: datetime.date

class CareLogCreate(CareLogBase):
    pass

class CareLog(CareLogBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True