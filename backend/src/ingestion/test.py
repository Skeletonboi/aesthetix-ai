# ChromaDB requires sqlite3>=3.35.0., so we substitute sqlite3 with pysqlite3 (pip install pysqlite3-binary )
__import__('pysqlite3')
import sys
import os
from pathlib import Path
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from src.chat.ingestion.utils import ChromaDBLocalGPUEmbedder

embed_model = ChromaDBLocalGPUEmbedder(model_name="Qwen/Qwen3-Embedding-0.6B", device="cuda")
vdb_path = os.path.join(Path(__file__).parents[0], 'chroma_db')
client = chromadb.PersistentClient(path=vdb_path)
col = client.get_collection(name="txtbks")
yt = client.get_collection(name="yt_transcripts")
res = col.query(query_texts=["Instruct: Find relevant documents \n Query: tricep tendinopathy"], include=['embeddings'])
res2 = yt.query(query_texts=["Instruct: Find relevant documents \n Query: tricep tendinopathy"], include=['embeddings'])
import code; code.interact(local=locals())