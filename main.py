import locale
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# UTF-8 인코딩 설정
try:
    locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass  # 기본 로케일 사용

from domain.user import user_router, user_model
from domain.diagnosis import diagnosis_router
from domain.care import care_router, care_model
from database.session import engine

user_model.Base.metadata.create_all(bind=engine)
care_model.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MINDI Backend API",
    description="치매 환자 케어 챗봇 서비스 백엔드 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정
origins = [
    "http://localhost:3000",
    "localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 사용자 관련 라우터를 앱에 포함시킵니다.
app.include_router(user_router.router, prefix="/api")
app.include_router(diagnosis_router.router, prefix="/api")
app.include_router(care_router.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Hello Mindi World"}
