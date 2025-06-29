from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

# APIRouter 인스턴스 생성
router = APIRouter()

# --- 설정 및 데이터베이스 (임시) ---
SECRET_KEY = "your-super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 비밀번호 해싱을 위한 컨텍스트 생성
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 임시 사용자 데이터베이스
fake_users_db = {}


# --- Pydantic 모델 정의 ---
# 1. 공통 필드를 위한 기본 모델
class UserBase(BaseModel):
    phone: str
    name: str
    gender: str
    birth_year: int
    birth_month: int
    birth_day: int
    education: str

# 2. 회원가입 시 클라이언트로부터 받을 데이터 모델 (입력용)
class UserCreate(UserBase):
    password: str

# 3. 데이터베이스에 저장될 데이터 모델
class UserInDB(UserBase):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    # Python 3.9 호환성을 위해 Union 또는 Optional 사용
    phone: Optional[str] = None


# --- 유틸리티 함수 ---
def verify_password(plain_password, hashed_password):
    """일반 비밀번호와 해시된 비밀번호를 비교합니다."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """비밀번호를 해시합니다."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """액세스 토큰을 생성합니다."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- API 엔드포인트 ---
@router.post("/signup", response_model=UserBase, tags=["Authentication"])
async def signup(user: UserCreate):
    """
    회원가입 엔드포인트. UserCreate 모델로 입력을 받고 UserBase 모델로 응답합니다.
    """
    if user.phone in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 전화번호입니다."
        )

    hashed_password = get_password_hash(user.password)

    # UserCreate 모델에서 일반 비밀번호를 제외하고, 해시된 비밀번호를 추가합니다.
    user_in_db = UserInDB(
        **user.model_dump(exclude={"password"}),
        hashed_password=hashed_password
    )

    # 데이터베이스에 저장합니다.
    fake_users_db[user.phone] = user_in_db.model_dump()

    # 클라이언트에게는 비밀번호 관련 정보가 없는 UserBase 모델을 반환합니다.
    return user_in_db

@router.post("/login", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    로그인 엔드포인트. 데이터베이스에서 사용자 정보를 가져와 비밀번호를 검증합니다.
    """
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="전화번호 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user = UserInDB(**user_dict)

    if not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="전화번호 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.phone}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}