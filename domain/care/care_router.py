from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import StreamingResponse
import boto3
from sqlalchemy.orm import Session
from datetime import date, timedelta

from config import settings
from domain.care import care_schema
from domain.user import user_schema
from database.session import get_db
from security import get_current_user
from . import care_crud

router = APIRouter(
    prefix="/care",
    tags=["Care"]
)

polly_client = boto3.Session(
    region_name=settings.AWS_REGION
).client('polly')

@router.post("/chat")
async def text_to_speech(
    text: str = Body(..., embed=True, description="음성으로 변환할 텍스트")
):
    try:
        # Amazon Polly API 호출
        response = polly_client.synthesize_speech(
            Engine='neural',            # 고품질 Neural 엔진 사용
            OutputFormat='mp3',         # 출력 포맷
            Text=text,                  # 변환할 텍스트
            VoiceId='Seoyeon'           # 한국어 음성 (서연)
        )

        audio_stream = response.get("AudioStream")

        if not audio_stream:
            raise HTTPException(status_code=500, detail="Polly API로부터 오디오 스트림을 받지 못했습니다.")

        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 변환 중 오류 발생: {str(e)}")

@router.post("/log", response_model=care_schema.CareLog)
def log_care_activity(
        db: Session = Depends(get_db),
        current_user: user_schema.User = Depends(get_current_user)
):
    return care_crud.create_care_log(db=db, owner_id=current_user.id)

@router.get("/logs/week", response_model=list[care_schema.CareLog])
def get_weekly_logs(
        db: Session = Depends(get_db),
        current_user: user_schema.User = Depends(get_current_user)
):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = today + timedelta(days=6)
    return care_crud.get_care_logs_for_week(
        db=db, owner_id=current_user.id, start_of_week=start_of_week, end_of_week=end_of_week
    )
