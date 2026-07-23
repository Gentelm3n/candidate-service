import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8080))

    PROVIDER_URL = os.getenv("PROVIDER_URL", "http://provider-simulator:8081")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/candidate.db")

    MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", 10))
    INITIAL_BACKOFF = float(os.getenv("INITIAL_BACKOFF", 1.0))
    MAX_BACKOFF = float(os.getenv("MAX_BACKOFF", 60.0))

    SCHEDULER_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL", 30))
    
config = Config()
