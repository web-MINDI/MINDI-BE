from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
import boto3
from config import settings

router = APIRouter(
    prefix="/care",
    tags=["Care"]
)

# Boto3를 사용하여 Polly 클라이언트를 생성합니다.
# EC2에 IAM 역할이 연결되어 있거나, 로컬에 aws configure가 설정되어 있으면
# access_key와 secret_key를 직접 넣지 않아도 자동으로 인증됩니다.
polly_client = boto3.Session(
    region_name=settings.AWS_REGION
).client('polly')

@router.post("/chat")
async def text_to_speech(
    text: str = Body(..., embed=True, description="음성으로 변환할 텍스트")
):
    """
    입력받은 텍스트를 Amazon Polly를 사용하여 음성 파일(mp3)로 변환하여 반환합니다.
    """
    try:
        # Amazon Polly API 호출
        response = polly_client.synthesize_speech(
            Engine='neural',            # 고품질 Neural 엔진 사용
            OutputFormat='mp3',         # 출력 포맷
            Text=text,                  # 변환할 텍스트
            VoiceId='Seoyeon'           # 한국어 음성 (서연)
        )

        # API 응답에서 오디오 스트림을 가져옵니다.
        audio_stream = response.get("AudioStream")

        if not audio_stream:
            raise HTTPException(status_code=500, detail="Polly API로부터 오디오 스트림을 받지 못했습니다.")

        # 스트리밍 응답으로 오디오를 바로 클라이언트에 전송합니다.
        # 이렇게 하면 서버에 파일을 저장하고 삭제하는 과정이 필요 없어 더 효율적입니다.
        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 변환 중 오류 발생: {str(e)}")

