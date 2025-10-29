__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from exa_py import Exa
from langchain.chat_models import init_chat_model

from src.config import Config
from src.auth.service import UserService
from src.workout_logs.service import WorkoutLogService
from src.ingestion.utils import ChromaDBLocalGPUEmbedder

class ResourcePool:
    has_initialized = False
    
    embedder = None
    chroma_client = None
    exa_client = None
    llm_chat_model = None
    user_service = None
    workout_logs_service = None
    
    @classmethod
    def initialize(cls, embed_model_bs=2):
        try:
            if not cls.embedder:
                cls.embedder = ChromaDBLocalGPUEmbedder(
                    model_name=Config.HF_EMBED_MODEL_NAME, 
                    device='cuda',
                    batch_size=embed_model_bs)
            
            if not cls.chroma_client:
                cls.chroma_client = chromadb.PersistentClient(path=Config.CHROMA_VDB_PATH)

            if not cls.exa_client:
                cls.exa_client = Exa(api_key=Config.EXA_API_KEY)
            
            if not cls.llm_chat_model:
                cls.llm_chat_model = init_chat_model(
                model=Config.CHAT_MODEL_NAME, 
                model_provider=Config.CHAT_MODEL_PROVIDER,
                api_key=Config.LLM_API_KEY)
            
            if not cls.user_service:
                cls.user_service = UserService()
            
            if not cls.workout_logs_service:
                cls.workout_logs_service = WorkoutLogService()
        except Exception as e:
            raise Exception(f"Failed to initialize a resource: {e}")
        
        cls.has_initialized = True