# Production Setup Guide - gpt-4.1-mini with Web Search

## ✅ OpenAI Web Search Integration

The backend uses **OpenAI's web search** to fetch real news articles with actual URLs!

### Installation

```bash
# Windows PowerShell
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## AI Configuration

All services use **gpt-4.1-mini**:

- ✅ **AIService** - Content generation, summaries, titles
- ✅ **NewsService** - Real news curation with OpenAI web search
- ✅ **NewsletterService** - Newsletter article generation

## How Web Search Works

The system uses **OpenAI's web_search tool**:

1. **Searches the web** for recent digital marketing news (last 7 days)
2. **Extracts real URLs** from actual news sites
3. **Generates catchy headlines** using AI power words
4. **Provides summaries** and business impact analysis

### Example Output:

```
✓ NewsService initialized with gpt-4.1-mini and web search
✓ Fetched 2 real news items for seo with web search

Title: Google Search Faces Market Share Reckoning: Below 90% for First Time...
URL: https://searchengineland.com/top-seo-news-stories-2025-466726
Publisher: Search Engine Land

Title: Adobe's $1.9B Semrush Acquisition Sparks AI Revolution...
URL: https://ignitevisibility.com/digital-marketing-news/
Publisher: Ignite Visibility
```

## Technical Implementation

```python
# Create LLM instance
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.7
)

# Bind web search tool
web_search_tool = {"type": "web_search"}
llm_with_search = llm.bind_tools([web_search_tool])

# Invoke with search
resp = await llm_with_search.ainvoke(prompt)
```

## Verify Installation

```bash
python -c "from app.services.news_service import NewsService; import asyncio; ns = NewsService(); result = asyncio.run(ns.fetch_news_with_catchy_titles('seo', 2)); print('✓ Fetched', len(result), 'items with URLs')"
```

Expected output:
```
✓ NewsService initialized with gpt-4.1-mini and web search
✓ Fetched 2 real news items for seo with web search
✓ Fetched 2 items with URLs
```

## Running the Backend

```bash
cd backend
.\venv\Scripts\activate
python main.py
```

Server starts on `http://0.0.0.0:8000`

## Features

✅ **Real news from the web** with actual URLs  
✅ **Catchy AI-generated headlines** with power words  
✅ **Business impact analysis**  
✅ **Automatic fallback** to AI-generated news if web search fails  
✅ **Production-ready** with gpt-4.1-mini  
✅ **No external dependencies** - uses OpenAI's native capabilities  

## Fallback Behavior

If web search fails, the system automatically falls back to AI-generated news, ensuring the application always works reliably.

## Dependencies

```
openai==1.109.1
langchain-openai==1.1.7
langchain-core==0.3.63
langchain==0.3.14
```

Clean, minimal dependencies - no external search tools needed!
