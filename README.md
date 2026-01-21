# Newsletter AI Backend

FastAPI-based backend service for the Editorial Digest Newsletter Generator. It powers the AI content generation, summarization, and integration with third-party services.

## Features

- **AI Content Generation**: Utilizes OpenAI (via LangChain) to generate newsletter summaries, headlines, and "Notes from the Editor".
- **Smart Summarization**: Context-aware summarization of news articles.
- **RESTful API**: Clean and documented API endpoints for the frontend.
- **CORS Support**: Configured for secure cross-origin requests from the frontend.

## Tech Stack

- **Framework**: FastAPI
- **Server**: Uvicorn
- **AI/LLM**: LangChain, OpenAI API
- **Language**: Python 3.9+

## Setup

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key.
- `SUPABASE_URL`: (Optional) For database integrations.
- `SUPABASE_KEY`: (Optional) For database integrations.

### 4. Run the Server

```bash
# Development mode with auto-reload
python main.py

# Or via uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once the server is running, you can access the interactive documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### AI Services
- `POST /api/ai/generate`: Generates specific content based on prompts.
- `POST /api/ai/summarize`: Summarizes input text or articles.
- `POST /api/ai/newsletter`: (If applicable) Generates full newsletter structure.

### Utility
- `GET /`: Root endpoint.
- `GET /health`: Health check endpoint.

## Project Structure

```
backend/
├── app/
│   ├── api/            # Route handlers
│   ├── services/       # Business logic and AI services
│   └── main.py         # App entry point
├── main.py             # Server entry point
├── requirements.txt    # Dependencies
└── README.md           # This file
```
