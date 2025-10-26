# ChromaDB requires sqlite3>=3.35.0., so we substitute sqlite3 with pysqlite3 (pip install pysqlite3-binary )
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from typing import List
import asyncio
from yt_transcript_util.yt_transcript import YoutubeTranscriptRetriever
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import json
from src.ingestion.summarizer import TranscriptSummarizer

# Could play around with making this a Pydantic model, using @model_validator(mode="before") @classmethod to fill each instance's class attributes/methods
class YoutubeIngestor():
    """
    Housing class for repeated ingestion operations:
    - periodic Youtube video transcript scraping, summarizing, vectorizing
    """
    def __init__(self, channel_ids: List, transcript_dir: str, hf_embed_model=None):
        self.channel_ids = channel_ids
        self.transcript_dir = transcript_dir
        
        # self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=hf_embed_model) if hf_embed_model else None
        self.embedding_func = hf_embed_model
        return
    
    def scrape_new_transcripts(self, yt_api_key, retry_failed):
        for channel_id in self.channel_ids:
            print(f'Processing channel ID: {channel_id} \n Retrieving transcripts...')
            retriever = YoutubeTranscriptRetriever(channel_id, yt_api_key, self.transcript_dir, retry_failed)
            _, _ = asyncio.run(retriever.scrape_transcripts())
        return

    def summarize_saved_transcripts(self, model_name):
        for channel_id in self.channel_ids:
            transcript_savepath = os.path.join(self.transcript_dir, "raw", f"{channel_id}.json")
            summary_savepath = os.path.join(self.transcript_dir, "summarized", f"{channel_id}.json")
            summarizer = TranscriptSummarizer(transcript_savepath=transcript_savepath)
            out, removed = summarizer.remove_empty(threshold=100)
            new_vids_dic, failed_vids = summarizer.summarize_transcripts(summary_savepath,
                                                                        model_name=model_name)
        return
    
    def vectorize_transcript_summaries(self, vdb_path):
        print("Beginning transcript vectorization ...")
        client = chromadb.PersistentClient(path=vdb_path)
        collection = client.create_collection(
            name="yt_transcripts", 
            embedding_function = self.embedding_func,
            get_or_create=True
            )

        existing_metas = collection.get(include=["metadatas"])
        existing_vid_ids = set(meta['vid_id'] for meta in existing_metas['metadatas'])

        for channel_id in self.channel_ids:
            print(f"Vectorizing transcripts from channel id: {channel_id} ...")
            # Load summaries
            summary_savepath = os.path.join(self.transcript_dir, "summarized", f"{channel_id}.json")
            try:
                with open(summary_savepath, "r") as f:
                    vids_dic = json.load(f)
            except Exception as e:
                print(f"Unable to open summary file of channel_id: {channel_id}, Error: {e}")
                break
            
            # Transcript summaries are ID'd by video ID
            vid_ids = [vid_id for vid_id in vids_dic.keys() if vid_id not in existing_vid_ids]
            vid_sums = [vids_dic[vid_id]['summary'] for vid_id in vid_ids]
            vid_metas = [{'vid_id': vid_id, 'title' : vids_dic[vid_id]['title']} for vid_id in vid_ids]
            
            if vid_ids:
                collection.upsert(
                    ids=vid_ids,
                    documents=vid_sums,
                    metadatas=vid_metas
                )
        print("Vectorization finished.")
        return