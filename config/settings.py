import os
from pathlib import Path
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 기본 디렉토리 설정
BASE_DIR = Path(__file__).resolve().parent.parent

# .env 파일 로드
env_file = BASE_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)

# 데이터베이스 설정
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "passwd": os.getenv("DB_PASSWORD", ""),
    "db": os.getenv("DB_NAME", "auto_daenak")
}

# MySQL Binlog 설정
BINLOG_CONFIG = {
    "tables": ["remote_pcs"],
    "schema": os.getenv("auto_daenak"),
}

# 재시도 설정
RETRY_CONFIG = {
    "max_retries": int(os.getenv("MAX_RETRIES", "5")),
    "retry_delay": int(os.getenv("RETRY_DELAY", "5"))
}

# 애플리케이션 설정
APP_CONFIG = {
    "service_name": "deanak",
    "log_dir": BASE_DIR / "logs",
    "unique_id_file": BASE_DIR / "unique_id.txt"
}