from sqlalchemy.orm import Session
from domain.user import user_model, user_schema

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
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
