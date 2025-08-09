from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status

from domain.user import user_model, user_schema
from security import decode_token
from database.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")

def get_user_by_phone(db: Session, phone: str):
    return db.query(user_model.User).filter(user_model.User.phone == phone).first()

def create_user(db: Session, user: user_schema.UserCreate, hashed_password: str):
    db_user = user_model.User(
        phone=user.phone,
        hashed_password=hashed_password,
        name=user.name,
        gender=user.gender,
        birth_year=user.birth_year,
        birth_month=user.birth_month,
        birth_day=user.birth_day,
        education=user.education,
        subscription_type=user.subscription_type or "standard",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db: Session, user_id: int):
    return db.query(user_model.User).filter(user_model.User.id == user_id).first()

def get_users_by_subscription_type(db: Session, subscription_types: list):
    """구독 타입별 사용자 목록 조회"""
    return db.query(user_model.User).filter(
        user_model.User.subscription_type.in_(subscription_types)
    ).all()

def update_subscription_type(db: Session, user_id: int, subscription_type: str):
    """사용자의 구독 타입을 업데이트"""
    user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not user:
        return None
    
    user.subscription_type = subscription_type
    db.commit()
    db.refresh(user)
    return user

def update_user_info(db: Session, user_id: int, name: str, gender: str, birth_year: int, birth_month: int, birth_day: int, education: str):
    """사용자 정보를 업데이트"""
    user = db.query(user_model.User).filter(user_model.User.id == user_id).first()
    if not user:
        return None
    
    user.name = name
    user.gender = gender
    user.birth_year = birth_year
    user.birth_month = birth_month
    user.birth_day = birth_day
    user.education = education
    
    db.commit()
    db.refresh(user)
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    phone: str = payload.get("sub")
    if phone is None:
        raise credentials_exception
    
    user = get_user_by_phone(db, phone=phone)
    if user is None:
        raise credentials_exception
    
    return user