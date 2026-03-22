from pydantic_settings import BaseSettings, SettingsConfigDict
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    # Short-lived access JWT (minutes). Typical for APIs: 15–30m.
    ACCESS_TOKEN_EXPIRY_MINUTES: int = 30
    # Long-lived refresh JWT (days). Typical consumer apps: 7–30d.
    REFRESH_TOKEN_EXPIRY: int = 14
    REDIS_URL: str
    REDIS_HOST: str
    REDIS_PORT: str
    OPENAI_API_KEY: str
    OPENROUTER_API_KEY: str
    EXA_API_KEY: str
    YT_API_KEY: str
    HF_EMBED_MODEL_NAME: str
    CHROMA_VDB_PATH: str
    TRANSCRIPT_PATH: str
    ML_SERVICE_ENDPOINT: str
    FRONTEND_URL: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    SESSION_SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(root_dir, ".env"),
        extra="ignore"
    )

Config = Settings()

if not os.path.isabs(Config.CHROMA_VDB_PATH):
    Config.CHROMA_VDB_PATH = os.path.join(root_dir, Config.CHROMA_VDB_PATH)

if not os.path.isabs(Config.TRANSCRIPT_PATH):
    Config.TRANSCRIPT_PATH = os.path.join(root_dir, Config.TRANSCRIPT_PATH)