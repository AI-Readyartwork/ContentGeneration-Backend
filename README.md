# Newsletter AI Backend

FastAPI backend with OpenAI integration for AI-powered newsletter generation.

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
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `SUPABASE_URL` - Your Supabase project URL (optional)
- `SUPABASE_KEY` - Your Supabase API key (optional)

### 4. Run the Server

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── ai_routes.py    # AI endpoints
│   └── services/
│       ├── __init__.py
│       └── ai_service.py   # OpenAI AI service
├── venv/                   # Virtual environment (not in git)
├── .env                    # Environment variables (not in git)
├── .env.example           # Example environment variables
├── .gitignore
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
└── README.md
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### AI Endpoints
- `POST /api/ai/generate` - Generate AI content
- `POST /api/ai/summarize` - Summarize text

## Development

### Adding New Routes

1. Create a new route file in `app/api/`
2. Import and include it in `app/api/__init__.py`

### Adding New Services

1. Create a new service file in `app/services/`
2. Import and use it in your routes

## Dependencies

- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **OpenAI** - OpenAI API client
- **Pydantic** - Data validation
- **python-dotenv** - Environment variable management

## Notes

- The backend uses OpenAI's API directly (no LangChain) to avoid compilation issues on Windows
- All dependencies are pure Python packages (no C/Rust compilation required)
- CORS is configured to allow requests from `http://localhost:5173` and `http://localhost:3000`
