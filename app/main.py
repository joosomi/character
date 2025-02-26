import logging
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import APP_HOST, APP_PORT
from app.routes.chat import router as chat_router
from app.routes.debug import router as debug_router

# 환경 변수 로드
load_dotenv()

# 로깅
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(title="Serenity API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 제공 설정
# 프로젝트 루트의 static 폴더를 확인
static_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"
)
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"정적 파일 디렉토리 '{static_dir}'가 마운트됨")
else:
    # app 폴더 내의 static 폴더 확인
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info(f"정적 파일 디렉토리 '{static_dir}'가 마운트됨")
    else:
        logger.warning("정적 파일 디렉토리를 찾을 수 없습니다")

# 라우터 등록
app.include_router(chat_router)
app.include_router(debug_router)


# 루트 경로 - index.html
@app.get("/", response_class=FileResponse)
async def get_index():
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 서버 실행 코드
if __name__ == "__main__":
    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=True)
