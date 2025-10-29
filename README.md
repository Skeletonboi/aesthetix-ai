# Aesthetix AI - Fitness Tracker + Intelligence Assistant

Custom fitness tracker with an AI assistant that integrates knowledge from fitness-science Youtube channels, research papers, and textbooks, to deliver both scientifically grounded and practically proven advice.

## Overview

Aesthetix-AI is built using a FastAPI backend for user workout tracking, with SQLAlchemy and PostgreSQL for CRUD operations. Exercises and workout logs are independently stored and tagged with exposed endpoints for full user customization and granular control.

The integrated AI-assistant uses Retrieval-Augmented Generation (RAG) on an automated data ingestion and summarization pipeline which includes automated scraping, cleaning, summarizing, and embedding of Youtube transcripts and textbooks. Embedding-based research paper retrieval and summarizaton is performed using Exa API.

## Features
- **AI Chat Assistant** - Ask any fitness/exercise question and get evidence-based answers
- **Custom Data Ingestion Pipeline** - Automated Youtube channel scraping, summarization, and vector embedding ingestion scripts
- **RAG-Powered Search** - Semantically searches across curated YouTube fitness content, research papers, and textbooks
- **Custom JWT Authentication + Redis cache** - Custom JWT-based route authentication with refresh tokens and redis blocklist caching
- **Full Exercise Customization** - Track and store any user-created exercise dynamically

## Data Workflow

1. **Ingestion** - YouTube transcripts, and textbooks are chunked and embedded with the selected HuggingFace embedding model
2. **Storage** - Embeddings stored in ChromaDB with metadata (video title, channel, timestamp)
3. **Query** - User query is embedded and similar chunks retrieved via vector retrieval
4. **Generation** - Retrieved context + user query sent to LLM for answer generation
5. **Response** - AI responds with answer and source citations


## Architecture

### Deployed Containers/Services

- **API Service** - workout log and exercise tracking, authentication, chat routing
- **ML Service** - data ingestion, scraping, vector embedding/retrieval, web search, and inference
- **Redis** - caching layer for JWT token management
- **PostgreSQL** - RDBMS storage for user data and fitness tracker data

### Tech Stack

**Backend:**
- FastAPI, SQLAlchemy, Pydantic, Alembic

**AI/ML:**
- LangChain/LangGraph, ChromaDB, Sentence Transformers, OpenAI, Exa, Docling
- [my custom python library for Youtube transcript scraping](https://github.com/Skeletonboi/yt-transcript-util)

**Infrastructure:**
- Docker, Redis, PostgreSQL

## Project Structure

```
aesthetix-ai/
├── backend/
│   ├── docker/
│   │   ├── api.Dockerfile
│   │   └── ml.Dockerfile
│   ├── src/
│   │   ├── auth/          # Authentication & user management
│   │   ├── chat/          # Chat routes, agents, and resource pool
│   │   ├── ingestion/     # YouTube transcript & content ingestion
│   │   ├── workout_logs/  # Workout tracking
│   │   ├── db/            # Database & Redis clients
│   │   ├── config.py      # Configuration management
│   │   └── main.py        # FastAPI app entry point
│   ├── migrations/        # Alembic database migrations
│   ├── data/              # Volume mounts for ChromaDB, transcripts
│   ├── docker-compose.yml
│   ├── requirements_api.txt
│   └── requirements_ml.txt
└── README.md
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- NVIDIA GPU (optional, for local ML service)
- API keys for OpenAI/Anthropic

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/aesthetix-ai.git
cd aesthetix-ai/backend
```

2. **Set your environment variables**
```
DATABASE_URL=<postgresql_database_url>
JWT_SECRET=<your_jwt_encryption_secret>
CHAT_MODEL_NAME=<your_chat_llm_model_name>
CHAT_MODEL_PROVIDER=<your_llm_provider i.e. openai>
LLM_API_KEY=<chat_model_api_key>
EXA_API_KEY=<exa_api_key>
HF_EMBED_MODEL_NAME=<hf_embedding_model_name>
YT_API_KEY=<youtube_data_api_key>

CHROMA_VDB_PATH=<local_chromadb_savepath>
TRANSCRIPT_PATH=<local_transcript_savepath>

REDIS_HOST=redis
REDIS_PORT=6379
```

3. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

Services will be available at:
- API: http://localhost:8000
- ML Service: http://localhost:8001
- Redis: localhost:6379
- 

## TBD

- [ ] Web and Mobile app frontend
- [ ] Advanced analytics and progress statistics
- [ ] Personalized training program generation
- [ ] Integration with fitness trackers (Apple Health, Google Fit)
- [ ] Community features and workout sharing


Copyright © 2025. All rights reserved.
For inquiries, contact: yp.victor@outlook.com
