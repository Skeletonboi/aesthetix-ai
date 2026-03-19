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
from langchain_openai import ChatOpenAI

# Custom chat model subclass to extract reasoning tokens 
class OpenRouterChat(ChatOpenAI):
    reasoning_enabled: bool = False

    @property
    def _llm_type(self) -> str:
        return "openrouter"

    @property
    def _default_params(self):
        params = super()._default_params
        params["extra_body"] = {"reasoning": {"enabled": self.reasoning_enabled}}
        return params

    def _create_chat_result(self, response, generation_info=None):
        """Override to extract reasoning from non-streaming responses."""
        result = super()._create_chat_result(response, generation_info)
        for gen, choice in zip(result.generations, response.choices):
            msg = choice.message
            reasoning = getattr(msg, "reasoning", None) or \
                        getattr(msg, "reasoning_content", None)
            if reasoning:
                gen.message.additional_kwargs["reasoning"] = reasoning
        return result

    def _convert_chunk_to_generation_chunk(self, chunk, default_chunk_class, base_generation_info=None):
        gen_chunk = super()._convert_chunk_to_generation_chunk(chunk, default_chunk_class, base_generation_info)
        if gen_chunk and chunk.get("choices"):
            delta = chunk["choices"][0].get("delta", {})
            reasoning = delta.get("reasoning") or delta.get("reasoning_content")
            if reasoning:
                gen_chunk.message.additional_kwargs["reasoning"] = reasoning
        return gen_chunk


class ResourcePool:
    has_initialized = False
    
    embedder = None
    chroma_client = None
    exa_client = None
    llm_chat_model = None
    user_service = None
    workout_logs_service = None

    _models = {} # {model_name[str] : model[BaseChatModel]}
    
    AVAILABLE_LLM_MODELS = { # dict of {model_name[str] : model_config{provider: str, api_key: str}
        'gpt-5-mini' : {
            'model_provider': 'openai', 
            'api_key': Config.OPENAI_API_KEY
        },
        'z-ai/glm-5' : {
            'api_key' : Config.OPENROUTER_API_KEY,
            'base_url' : 'https://openrouter.ai/api/v1'
        },
    }
    
    DEFAULT_LLM_MODEL = "z-ai/glm-5"

    @classmethod
    def get_model(cls, model_name: str | None = None):
        # Default if model_name is null
        model_name = model_name or cls.DEFAULT_LLM_MODEL
        # Specific check if the user provided invalid model_name
        if model_name not in cls._models:
            raise Exception(f"Unsupported or uninitialized model: {model_name} \n")
        return cls._models.get(model_name)

    @classmethod
    def initialize(cls, embed_model_bs=2):
        try:
            for model_name, model_config in cls.AVAILABLE_LLM_MODELS.items():
                if model_name == 'z-ai/glm-5':
                    cls._models[model_name] = OpenRouterChat(model=model_name, **model_config)
                if model_name not in cls._models:
                    cls._models[model_name] = init_chat_model(model=model_name, **model_config)
        except Exception as e:
            raise Exception(f"Failed to initialize a LLM chat model \n Error msg: {e}")

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
            
            if not cls.user_service:
                cls.user_service = UserService()
            
            if not cls.workout_logs_service:
                cls.workout_logs_service = WorkoutLogService()
        except Exception as e:
            raise Exception(f"Failed to initialize a resource \n Error msg: {e}")
        
        cls.has_initialized = True
    
    @classmethod
    def get_available_models(cls):
        return list(cls._models.keys())