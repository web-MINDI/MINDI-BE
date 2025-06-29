from fastapi import FastAPI
# CORS를 허용하기 위해 Middleware를 추가합니다.
from fastapi.middleware.cors import CORSMiddleware
from routers import auth  # 라우터 import

app = FastAPI()

# CORS 미들웨어 설정
origins = [
    "http://localhost:3000",  # React 개발 서버 주소
    "localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인증 라우터를 앱에 포함시킵니다.
app.include_router(auth.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Hello Mindi World"}
