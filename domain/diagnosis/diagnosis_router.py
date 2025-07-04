import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
from pydub import AudioSegment

# APIRouter 인스턴스 생성
router = APIRouter(
    prefix="/diagnosis",
    tags=["Diagnosis"]
)

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
