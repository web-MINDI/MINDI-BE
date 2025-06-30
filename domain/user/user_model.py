from sqlalchemy import Column, Integer, String
from database.session import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    gender = Column(String(10))
    birth_year = Column(Integer)
    birth_month = Column(Integer)
    birth_day = Column(Integer)
    education = Column(String(50))
