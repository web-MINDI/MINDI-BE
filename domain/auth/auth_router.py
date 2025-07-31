from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from database import session
from domain.user import user_crud, user_schema
from security import verify_password, create_token_pair, verify_refresh_token, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/refresh", response_model=user_schema.Token)
async def refresh_token(
    refresh_token_request: user_schema.RefreshTokenRequest,
    db: Session = Depends(session.get_db)
):
    """
    Refresh token을 사용하여 새로운 access token을 발급받습니다.
    """
    try:
        # Refresh token 검증
        payload = verify_refresh_token(refresh_token_request.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 사용자 정보 확인
        phone = payload.get("sub")
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_crud.get_user_by_phone(db, phone=phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 새로운 access token 생성
        access_token = create_access_token(data={"sub": phone})
        
        # 새로운 refresh token도 생성 (선택사항)
        new_refresh_token = create_refresh_token(data={"sub": phone})
        
        return user_schema.Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/validate")
async def validate_token(
    current_user: user_schema.User = Depends(user_crud.get_current_user)
):
    """
    현재 access token의 유효성을 검증하고 사용자 정보를 반환합니다.
    """
    return {
        "id": current_user.id,
        "phone": current_user.phone,
        "name": current_user.name,
        "email": current_user.email,
        "is_active": current_user.is_active
    } 