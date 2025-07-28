from fastapi import APIRouter, HTTPException, Body, Depends, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
import boto3
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
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
async def audio_to_answer(
    file: UploadFile = File(...),
    messages: str = Form(...),
    conversation_id: str = Form(...),  # 대화 세션 ID 추가
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
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
    # AI 서버로 wav 파일 + messages 전송
    with open(wav_path, "rb") as wav_file:
        files = {"file": (wav_filename, wav_file, "audio/wav")}
        data = {"messages": messages}
        async with httpx.AsyncClient() as client:
            ai_response = await client.post(AI_STT_REPLY_URL, files=files, data=data, timeout=30)
            if ai_response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI 서버 오류")
            ai_data = ai_response.json()
            user_text = ai_data.get("user_text")  # 사용자 질문
            ai_reply = ai_data.get("reply")       # AI 답변
            if not user_text or not ai_reply:
                raise HTTPException(status_code=500, detail="AI 응답이 올바르지 않습니다.")
    # os.remove(raw_path)
    # os.remove(wav_path)
    # Polly TTS 변환
    tts_response = polly_client.synthesize_speech(
        Engine='neural',
        OutputFormat='mp3',
        Text=ai_reply,
        VoiceId='Seoyeon'
    )
    audio_stream = tts_response.get("AudioStream")
    if not audio_stream:
        raise HTTPException(status_code=500, detail="Polly API로부터 오디오 스트림을 받지 못했습니다.")
    # DB에 CareLog 저장 (완전한 대화 저장)
    care_log = care_crud.CareLogCreate(
        user_id=current_user.id,
        user_question=user_text,        # 사용자 질문 저장
        ai_reply=ai_reply,              # AI 답변 저장
        conversation_date=date.today(),
        conversation_id=conversation_id  # 대화 세션 ID 저장
    )
    care_log_id = care_crud.create_care_log(db=db, care_log=care_log)
    # 음성 파일만 반환 (텍스트는 DB에 저장됨)
    return StreamingResponse(audio_stream, media_type="audio/mpeg")

@router.post("/last-ai-reply")
def get_last_ai_reply(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    log = care_crud.get_last_care_log_by_user(db, user_id=current_user.id)
    if not log:
        raise HTTPException(status_code=404, detail="최근 AI 답변이 없습니다.")
    return {"ai_reply": log.ai_reply, "user_question": log.user_question}

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

@router.get("/conversation/{conversation_id}", response_model=list[care_schema.CareLog])
def get_conversation_logs(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """특정 대화 세션의 모든 로그 조회"""
    logs = care_crud.get_care_logs_by_conversation_id(db, conversation_id)
    if not logs:
        raise HTTPException(status_code=404, detail="대화 세션을 찾을 수 없습니다.")
    return logs

@router.get("/conversation/{conversation_id}/summary")
def get_conversation_summary(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """대화 세션 요약 정보 조회"""
    summary = care_crud.get_conversation_summary(db, conversation_id)
    if not summary:
        raise HTTPException(status_code=404, detail="대화 세션을 찾을 수 없습니다.")
    return summary

@router.get("/conversation/{conversation_id}/latest")
def get_latest_conversation_text(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """특정 대화 세션의 최신 대화 내용 조회 (텍스트만)"""
    log = care_crud.get_latest_care_log_by_conversation(db, conversation_id)
    if not log:
        raise HTTPException(status_code=404, detail="대화 내용을 찾을 수 없습니다.")
    return {
        "user_question": log.user_question,
        "ai_reply": log.ai_reply,
        "created_at": log.created_at
    }

@router.get("/conversation/{conversation_id}/all")
def get_all_conversation_texts(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """특정 대화 세션의 모든 대화 내용 조회 (텍스트만)"""
    logs = care_crud.get_care_logs_by_conversation_id(db, conversation_id)
    if not logs:
        raise HTTPException(status_code=404, detail="대화 세션을 찾을 수 없습니다.")
    return [
        {
            "user_question": log.user_question,
            "ai_reply": log.ai_reply,
            "created_at": log.created_at
        }
        for log in logs
    ]

@router.post("/conversation/start")
def start_conversation(
    current_user: user_schema.User = Depends(get_current_user)
):
    """대화 세션 시작: 새로운 conversation_id 발급"""
    conversation_id = str(uuid.uuid4())
    start_time = datetime.now().isoformat()
    return {"conversation_id": conversation_id, "start_time": start_time}

@router.post("/conversation/end/{conversation_id}")
def end_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """대화 세션 종료: 해당 세션의 로그 요약 반환"""
    logs = care_crud.get_care_logs_by_conversation_id(db, conversation_id)
    if not logs:
        raise HTTPException(status_code=404, detail="대화 세션을 찾을 수 없습니다.")
    # 간단 요약: turn 수, 시작/종료 시각, 최근 질문/답변
    summary = {
        "conversation_id": conversation_id,
        "turn_count": len(logs),
        "start_time": logs[0].created_at if logs else None,
        "end_time": logs[-1].created_at if logs else None,
        "last_user_question": logs[-1].user_question if logs else None,
        "last_ai_reply": logs[-1].ai_reply if logs else None
    }
    return summary
