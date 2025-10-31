from pydantic_settings import BaseSettings, SettingsConfigDict
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    REFRESH_TOKEN_EXPIRY: int
    REDIS_URL: str
    REDIS_HOST: str
    REDIS_PORT: str
    LLM_API_KEY: str
    EXA_API_KEY: str
    YT_API_KEY: str
    HF_EMBED_MODEL_NAME: str
    CHAT_MODEL_NAME: str
    CHAT_MODEL_PROVIDER: str
    CHROMA_VDB_PATH: str
    TRANSCRIPT_PATH: str
    ML_SERVICE_ENDPOINT: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(root_dir, ".env"),
        extra="ignore"
    )

Config = Settings()

if not os.path.isabs(Config.CHROMA_VDB_PATH):
    Config.CHROMA_VDB_PATH = os.path.join(root_dir, Config.CHROMA_VDB_PATH)

if not os.path.isabs(Config.TRANSCRIPT_PATH):
    Config.TRANSCRIPT_PATH = os.path.join(root_dir, Config.TRANSCRIPT_PATH)