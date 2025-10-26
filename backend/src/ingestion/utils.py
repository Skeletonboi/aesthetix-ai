# ChromaDB requires sqlite3>=3.35.0., so we substitute sqlite3 with pysqlite3 (pip install pysqlite3-binary )
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from chromadb import EmbeddingFunction, Documents, Embeddings
from sentence_transformers import SentenceTransformer
import torch

class ChromaDBLocalGPUEmbedder(EmbeddingFunction[Documents]):
    """
    Custom ChromaDB Embedding Function to utilize GPU (cuda) w/ HF models
    """
    def __init__(self, model_name: str, device="cuda", batch_size=2):
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = 2
    
    def __call__(self, input: Documents) -> Embeddings:
        with torch.no_grad():
            all_embeddings = []
            for i in range(0, len(input), self.batch_size):
                all_embeddings += self.model.encode(input[i:i + self.batch_size], convert_to_numpy=True).tolist()
            return all_embeddings
        # return self.model.encode(input, convert_to_numpy=True).tolist()