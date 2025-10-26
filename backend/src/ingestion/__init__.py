"""
ML Ingestion Module

This module provides components for ingesting and processing YouTube transcript data
for the Aesthetix AI backend.

Components:
- YouTubeIngestionPipeline: Complete pipeline for transcript processing
- TranscriptSummarizer: LLM-based transcript summarization
- TranscriptEmbedder: Embedding generation for vector search
"""

from .yt_ingestor import YoutubeIngestor
from .summarizer import TranscriptSummarizer, TranscriptProcessor

__all__ = [
    "YoutubeIngestor",
    "TranscriptSummarizer", 
    "TranscriptProcessor",
]