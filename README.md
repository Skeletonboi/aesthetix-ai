# Aesthetix AI - Fitness Tracker + Intelligence Assistant

Custom fitness tracker with an AI assistant that integrates knowledge from fitness-science Youtube channels, research papers, and textbooks, to deliver both scientifically grounded and practically proven advice.

## 🎯 Overview

Aesthetix-AI is built using a FastAPI backend for user workout tracking, with SQLAlchemy and PostgreSQL for CRUD operations. Exercises and workout logs are independently stored and tagged with exposed endpoints for full user customization and granular control.

The integrated AI-assistant uses Retrieval-Augmented Generation (RAG) on a custom automated data ingestion and summarization pipeline which includes automated scraping, cleaning, summarizing, and embedding of Youtube transcripts and textbooks. Embedding-based research paper retrieval and summarizaton is performed using Exa API.  

## ✨ Features
- **AI Chat Assistant** - Ask any fitness/exercise question and get evidence-based answers
- **RAG-Powered Search** - Semantically searches across curated YouTube fitness content, research papers, and textbooks
- **Custom JWT Authentication + Redis cache** - Custom JWT-based route authentication with refresh tokens and redis blocklist caching
- **Full Exercise Customization** - Track and store any user-created exercise dynamically
- **Vector Embeddings** - ChromaDB for semantic search across fitness knowledge base

## 🏗️ Architecture

### Services

- **API Service** - Authentication, workout log / exercise creation, and chat routing
- **ML Service** - Embedding, vector retrieval, and LLM inference
- **Redis** - Caching layer for JWT token management
- **PostgreSQL** - Storage for user data and fitness tracker data

### Tech Stack

**Backend:**
- FastAPI, SQLAlchemy, Pydantic, Alembic

**AI/ML:**
- LangChain, LangGraph, ChromaDB, Sentence Transformers, OpenAI
- [Custom Youtube Transcript Scraping Library](https://github.com/Skeletonboi/yt-transcript-util)

**Infrastructure:**
- Docker, Redis, PostgreSQL, Playwright

## 📁 Project Structure

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

## 🚀 Getting Started

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

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and database URLs
```

Required variables:
```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_HOST=redis
REDIS_PORT=6379
JWT_SECRET=your-secret-key
LLM_API_KEY=your-openai-key
EXA_API_KEY=your-exa-key
CHROMA_VDB_PATH=/repo/data/chroma_db
```

3. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

Services will be available at:
- API: http://localhost:8000
- ML Service: http://localhost:8001
- Redis: localhost:6379

## 🧠 How It Works

1. **Ingestion** - YouTube transcripts are chunked and embedded using Sentence Transformers
2. **Storage** - Embeddings stored in ChromaDB with metadata (video title, channel, timestamp)
3. **Query** - User question is embedded and similar chunks retrieved via vector retrieval
4. **Generation** - Retrieved context + user query sent to LLM for answer generation
5. **Response** - AI responds with answer and source citations

## 📊 Data Sources

Currently ingesting from:
- Select fitness-science Youtube Channels
- Research papers (PubMed)
- Fitness textbooks

## 🚧 Roadmap

- [ ] Web and Mobile app frontend
- [ ] Advanced analytics and progress statistics
- [ ] Personalized training program generation
- [ ] Integration with fitness trackers (Apple Health, Google Fit)
- [ ] Community features and workout sharing

## 📝 License

Copyright © 2025. All rights reserved.

## 📧 Contact

For inquiries, contact: yp.victor@outlook.com

---

**Note:** This project is under active development. Features and documentation may change.

