import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pathlib import Path
from pydub import AudioSegment
import httpx
import os
import uuid
from sqlalchemy.orm import Session
from datetime import datetime

from database.session import get_db
from domain.user import user_schema, user_crud
from security import get_current_user

# APIRouter 인스턴스 생성
router = APIRouter(
    prefix="/diagnosis",
    tags=["Diagnosis"]
)

# AI 서버 URL
AI_DIAGNOSIS_URL = "http://localhost:8001/diagnose"

# 녹음 파일을 저장할 디렉토리 설정
UPLOAD_DIRECTORY = Path("uploads/")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

@router.post("/upload-audio")
async def upload_audio(
    question_id: str = Form(...),
    audio_file: UploadFile = File(...)
):
    original_filename_stem = Path(audio_file.filename).stem
    wav_filename = f"answer{question_id}.wav"
    save_path = UPLOAD_DIRECTORY / wav_filename

    temp_file_path = UPLOAD_DIRECTORY / audio_file.filename
    try:
        with open(temp_file_path, "wb+") as file_object:
            shutil.copyfileobj(audio_file.file, file_object)

        audio = AudioSegment.from_file(temp_file_path)
        audio.export(save_path, format="wav")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오디오 파일 변환에 실패했습니다: {e}")
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()
        audio_file.file.close()

    return {
        "info": f"File '{audio_file.filename}' converted to wav and saved at '{save_path}'",
        "filename": wav_filename
    }

@router.post("/audio-to-diagnosis")
async def audio_to_diagnosis(
    file: UploadFile = File(...),
    question_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """음성 파일을 AI 서버로 전송하여 저장 - ko_model.py 방식"""
    
    # 1. 파일 저장 및 wav 변환
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
    
    # 2. AI 서버로 wav 파일 전송 (파일만 저장)
    try:
        with open(wav_path, "rb") as wav_file:
            files = {"file": (wav_filename, wav_file, "audio/wav")}
            data = {
                "question_id": question_id,
                "user_id": current_user.id
            }
            
            async with httpx.AsyncClient() as client:
                ai_response = await client.post(
                    AI_DIAGNOSIS_URL, 
                    files=files, 
                    data=data, 
                    timeout=30
                )
                
                if ai_response.status_code != 200:
                    raise HTTPException(status_code=500, detail="AI 서버 파일 저장 오류")
                
                ai_data = ai_response.json()
                return ai_data
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="AI 서버 응답 시간 초과")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 서버 통신 오류: {e}")
    finally:
        # 임시 파일 정리
        if os.path.exists(raw_path):
            os.remove(raw_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

@router.post("/start-diagnosis")
async def start_diagnosis(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """진단 세션 시작"""
    
    # 사용자 정보 조회
    user = user_crud.get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자 정보를 찾을 수 없습니다.")
    
    # 진단 세션 정보 반환
    diagnosis_session = {
        "session_id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "start_time": datetime.now().isoformat(),
        "total_questions": 21
    }
    
    return diagnosis_session

@router.post("/submit-diagnosis")
async def submit_diagnosis(
    session_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """전체 진단 결과 제출 및 최종 진단 - ko_model.py 방식"""
    
    try:
        user = user_crud.get_user_by_id(db, current_user.id)
        user_age = datetime.now().year - user.birth_year
        user_education = getattr(user, 'education', '대학교')
        
        # AI 서버에 최종 진단 요청 (모든 파일을 한번에 처리)
        diagnosis_data = {
            "session_id": session_id,
            "user_id": current_user.id,
            "user_age": user_age,
            "user_education": user_education
        }
        
        async with httpx.AsyncClient() as client:
            ai_response = await client.post(
                f"{AI_DIAGNOSIS_URL}/final",
                json=diagnosis_data,
                timeout=120  # 전체 진단은 더 오래 걸림
            )
            
            if ai_response.status_code != 200:
                raise HTTPException(status_code=500, detail="AI 서버 최종 진단 오류")
            
            diagnosis_result = ai_response.json()
            
            # TODO: 진단 결과를 데이터베이스에 저장
            # diagnosis_crud.create_diagnosis_log(db, diagnosis_result)
            
            return diagnosis_result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"진단 제출 오류: {e}")

@router.get("/diagnosis-history")
async def get_diagnosis_history(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    """사용자의 진단 기록 조회"""
    
    # TODO: 진단 기록 조회 로직 구현
    # history = diagnosis_crud.get_diagnosis_history(db, current_user.id)
    
    # 임시 응답
    return {
        "message": "진단 기록 조회 기능은 아직 구현 중입니다.",
        "user_id": current_user.id
    }
