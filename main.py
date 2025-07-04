from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domain.user import user_router, user_model
from domain.diagnosis import diagnosis_router
from database.session import engine

user_model.Base.metadata.create_all(bind=engine)

app = FastAPI()

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

@app.get("/")
async def root():
    return {"message": "Hello Mindi World"}
