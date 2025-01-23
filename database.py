import asyncio
import os
import sys
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 실행 파일 또는 스크립트의 디렉토리 경로 가져오기
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 경우
    application_path = os.path.dirname(sys.executable)
else:
    # 일반 Python 스크립트로 실행된 경우
    application_path = os.path.dirname(os.path.abspath(__file__))

# .env 파일 경로 설정
env_path = os.path.join(application_path, '.env')

# .env 파일에서 환경 변수 로드
load_dotenv(env_path)

# 데이터베이스 설정 (MySQL)
DATABASE_URL = f"mysql+aiomysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

# 비동기 엔진 생성
async_engine = create_async_engine(DATABASE_URL, echo=False)

# 비동기 세션 설정
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

# async with 구문에서 사용하기 위한 비동기 컨텍스트 매니저 함수
@asynccontextmanager
async def get_db_context():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
