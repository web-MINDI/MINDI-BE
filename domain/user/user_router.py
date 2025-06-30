from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from domain.user import user_schema, user_crud
import security
from database.session import get_db

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post("/signup", response_model=user_schema.User)
def signup(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    db_user = user_crud.get_user_by_phone(db, phone=user.phone)
    if db_user:
        raise HTTPException(
            status_code=400, detail="이미 등록된 전화번호입니다."
        )
    hashed_password = security.get_password_hash(user.password)
    return user_crud.create_user(db=db, user=user, hashed_password=hashed_password)


@router.post("/login", response_model=user_schema.Token)
def login_for_access_token(
        db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = user_crud.get_user_by_phone(db, phone=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="전화번호 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(data={"sub": user.phone})
    return {"access_token": access_token, "token_type": "bearer"}
