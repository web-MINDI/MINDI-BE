from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from domain.user import user_schema, user_crud
import security
from database.session import get_db

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

# 현재 사용자 가져오기
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 인증 정보입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = security.decode_token(token)
        phone: str = payload.get("sub")
        if phone is None:
            raise credentials_exception
    except:
        raise credentials_exception
    
    user = user_crud.get_user_by_phone(db, phone=phone)
    if user is None:
        raise credentials_exception
    return user

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

    # Access token과 refresh token 쌍 생성
    access_token, refresh_token = security.create_token_pair(data={"sub": user.phone})
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/validate", response_model=user_schema.User)
async def validate_token(current_user = Depends(get_current_user)):
    """토큰 유효성 검증 및 현재 사용자 정보 반환"""
    return current_user

@router.get("/me", response_model=user_schema.User)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return current_user
