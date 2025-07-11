from fastapi import APIRouter, HTTPException, Body, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
import boto3
from sqlalchemy.orm import Session
from datetime import date, timedelta
import httpx
import shutil
import os
import uuid
from pydub import AudioSegment

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

AI_STT_REPLY_URL = "http://localhost:8001/stt-and-reply"

def polly_tts(text: str):
    response = polly_client.synthesize_speech(
        Engine='neural',
        OutputFormat='mp3',
        Text=text,
        VoiceId='Seoyeon'
    )
    audio_stream = response.get("AudioStream")
    if not audio_stream:
        raise HTTPException(status_code=500, detail="Polly API로부터 오디오 스트림을 받지 못했습니다.")
    return StreamingResponse(audio_stream, media_type="audio/mpeg")

@router.post("/audio-to-answer")
async def audio_to_answer(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    ext = (file.filename.split('.')[-1] if file.filename and '.' in file.filename else 'webm')
    raw_filename = f"{uuid.uuid4()}.{ext}"
    raw_path = os.path.join("uploads", raw_filename)
    with open(raw_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # wav 변환
    wav_filename = raw_filename.rsplit('.', 1)[0] + ".wav"
    wav_path = os.path.join("uploads", wav_filename)
    try:
        audio = AudioSegment.from_file(raw_path)
        audio.export(wav_path, format="wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"wav 변환 실패: {e}")
    # AI 서버로 wav 파일 전송
    with open(wav_path, "rb") as wav_file:
        files = {"file": (wav_filename, wav_file, "audio/wav")}
        async with httpx.AsyncClient() as client:
            ai_response = await client.post(AI_STT_REPLY_URL, files=files)
            if ai_response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI 서버 오류")
            ai_data = ai_response.json()
            ai_reply = ai_data.get("reply")
            if not ai_reply:
                raise HTTPException(status_code=500, detail="AI 답변이 비어 있습니다.")
    # os.remove(raw_path)
    # os.remove(wav_path)
    return polly_tts(ai_reply)

@router.post("/greeting")
async def greeting():
    greeting_text = "안녕하세요! 민디입니다. 오늘 하루는 어떠셨나요?"
    return polly_tts(greeting_text)

@router.post("/log", response_model=care_schema.CareLog)
def log_care_activity(
    care_log: care_schema.CareLogCreate,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    # user_id를 강제로 현재 로그인 사용자로 세팅
    care_log_data = care_log.dict()
    care_log_data["user_id"] = current_user.id
    return care_crud.create_care_log(db=db, care_log=care_schema.CareLogCreate(**care_log_data))

@router.get("/last-log", response_model=care_schema.CareLog)
def get_last_log(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    log = care_crud.get_last_care_log_by_user(db, user_id=current_user.id)
    if not log:
        raise HTTPException(status_code=404, detail="No log found for user.")
    return log

@router.get("/logs/week", response_model=list[care_schema.CareLog])
def get_weekly_logs(
        db: Session = Depends(get_db),
        current_user: user_schema.User = Depends(get_current_user)
):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = today + timedelta(days=6)
    return care_crud.get_care_logs_for_week(
        db=db, user_id=current_user.id, start_of_week=start_of_week, end_of_week=end_of_week
    )
