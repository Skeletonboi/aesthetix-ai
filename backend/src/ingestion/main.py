# 'UC68TLK0mAEzUyHx5x5k-S1Q' # Jeff Nippard
# 'UCBk3GhTT4sTwRwQJAchgTUw' # Scientific Snitch
# 'UCERm5yFZ1SptUEU4wZ2vJvw' # Jeremy Ethier
# 'UCJLtThHoSMSKw6rbEcyhkpQ' # Lyle McDonald
# 'UClHVl2N3jPEbkNJVx-ItQIQ' # HealthyGamerGG
# 'UCObA5o3mcc1felIMAv6cukw' # Geoffrey Verity Schofield
# 'UCru8Ef3TDFaJOOTfAZ52iFA' # Dr.Milo Wolf
# 'UC_7lEuEKvFt63jtvZYwlHMQ' # Eugene Teo
# 'UCf33v9eZOy59r7HM44ni_4Q' # BasementBodybuilding

from src.ingestion.utils import ChromaDBLocalGPUEmbedder
from src.ingestion.yt_ingestor import YoutubeIngestor
from src.config import Config

YT_API_KEY = Config.YT_API_KEY
HF_EMBED_MODEL_NAME = Config.HF_EMBED_MODEL_NAME
TRANSCRIPT_PATH = Config.TRANSCRIPT_PATH
CHROMA_VDB_PATH = Config.CHROMA_VDB_PATH
# Youtube channels to scrape transcripts from
CHANNEL_IDS = [
    'UC68TLK0mAEzUyHx5x5k-S1Q', 
    'UCBk3GhTT4sTwRwQJAchgTUw', 
    'UCERm5yFZ1SptUEU4wZ2vJvw', 'UCJLtThHoSMSKw6rbEcyhkpQ', 
    'UCObA5o3mcc1felIMAv6cukw', 'UCru8Ef3TDFaJOOTfAZ52iFA',
    'UC_7lEuEKvFt63jtvZYwlHMQ', 'UCf33v9eZOy59r7HM44ni_4Q'
]

if __name__ ==  '__main__':
    # Check for (new) transcripts and scrape
    embed_model = ChromaDBLocalGPUEmbedder(model_name=HF_EMBED_MODEL_NAME, device="cuda")
    yt_ingestor = YoutubeIngestor(channel_ids=CHANNEL_IDS, transcript_dir=TRANSCRIPT_PATH, hf_embed_model=embed_model)
    _ = yt_ingestor.scrape_new_transcripts(YT_API_KEY, retry_failed=True)
    _ = yt_ingestor.summarize_saved_transcripts(model_name='gpt-5-mini')
    _ = yt_ingestor.vectorize_transcript_summaries(vdb_path=CHROMA_VDB_PATH)
    