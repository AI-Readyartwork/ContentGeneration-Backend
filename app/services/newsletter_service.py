"""
Newsletter content generation service using LangChain
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Optional
from datetime import datetime

from app.config import settings
from app.models.news import NewsItem


def get_current_date_context() -> str:
    """Get current date context string for prompts"""
    now = datetime.now()
    return f"CURRENT DATE: {now.strftime('%B %d, %Y')} (Year: {now.year}). All content should be relevant to {now.year}, not past years."


# Updated sections - removed tomorrow-top and main-article (main-article is AI-generated from main-story)
DEFAULT_SECTIONS = [
    {"key": "main-story", "title": "Main Story", "description": "The headline story with hook title", "min_items": 1, "max_items": 1},
    {"key": "main-story-summary", "title": "Main Story Summary", "description": "AI-generated summary of main story", "min_items": 1, "max_items": 1},
    {"key": "second-story", "title": "Second Story", "description": "Supporting story with 400-500 word article", "min_items": 1, "max_items": 1},
    {"key": "third-story", "title": "Third Story", "description": "Additional story with 400-500 word article", "min_items": 1, "max_items": 1},
    {"key": "trendsetter", "title": "Trendsetter", "description": "One-liners with hyperlinks for emerging trends", "min_items": 1, "max_items": 3},
    {"key": "top-news", "title": "Top Digital Marketing News", "description": "One-liners with hyperlinks", "min_items": 2, "max_items": 5},
    {"key": "links", "title": "Links that Don't Suck", "description": "Valuable resources with hyperlinks", "min_items": 2, "max_items": 5},
]


class NewsletterService:
    def __init__(self):
        # Using gpt-4.1-mini for production newsletter generation
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        self.str_parser = StrOutputParser()
    
    def get_sections(self) -> List[Dict]:
        """Return available newsletter sections"""
        return DEFAULT_SECTIONS

    async def generate_ai_article(
        self,
        main_story: NewsItem,
        supporting_items: List[NewsItem] = None,
        style: str = "professional"
    ) -> str:
        """Generate a long-form AI article based on the main story"""
        supporting_context = ""
        if supporting_items:
            supporting_context = "\n".join([
                f"- {item.title}: {item.summary}" 
                for item in supporting_items[:3]
            ])
        
        date_context = get_current_date_context()
        current_year = datetime.now().year
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

You are a senior digital marketing journalist writing for a B2B newsletter in {current_year}.

Write a comprehensive 600-800 word feature article that:
- Opens with a compelling narrative hook
- Provides deep analysis of the topic
- Includes industry context and trends for {current_year}
- Offers strategic insights and predictions
- Provides 3-4 actionable takeaways
- Ends with a thought-provoking conclusion

IMPORTANT: We are in {current_year}. Do NOT reference 2024 or past years as current.

TONE: {{style}}, authoritative, insightful
FORMAT: Use subheadings, short paragraphs, and bullet points where appropriate."""),
            ("user", """Write the main feature article:

Main Story: {{title}}
Summary: {{summary}}
Why It Matters: {{why_it_matters}}

Supporting Context:
{{supporting_context}}""")
        ])
        
        chain = prompt | self.llm | self.str_parser
        
        try:
            result = await chain.ainvoke({
                "style": style,
                "title": main_story.title,
                "summary": main_story.summary or "No summary provided",
                "why_it_matters": main_story.why_it_matters or "Impact to be determined",
                "supporting_context": supporting_context or "No additional context"
            })
            return result.strip()
        except Exception as e:
            print(f"Error generating article: {e}")
            return ""

    async def generate_story_content(
        self,
        title: str,
        summary: str = "",
        word_count: int = 450
    ) -> str:
        """Generate 400-500 word story content for second/third stories"""
        date_context = get_current_date_context()
        current_year = datetime.now().year
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

You are a digital marketing journalist writing engaging articles in {current_year}.

Write a {{word_count}} word article that:
- Opens with a strong hook
- Explains the news and its context
- Discusses business implications
- Provides actionable insights
- Ends with a forward-looking statement

IMPORTANT: We are in {current_year}. Do NOT reference 2024 or past years as current.

Use short paragraphs (2-3 sentences) for readability."""),
            ("user", "Write an article about:\n\nTitle: {{title}}\nContext: {{summary}}")
        ])
        
        chain = prompt | self.llm | self.str_parser
        
        try:
            result = await chain.ainvoke({
                "word_count": word_count,
                "title": title,
                "summary": summary or "No additional context"
            })
            return result.strip()
        except Exception as e:
            print(f"Error generating story: {e}")
            return ""

    async def generate_one_liner(self, title: str) -> str:
        """Generate a one-liner for Trendsetter/Top News sections"""
        date_context = get_current_date_context()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

Write a punchy one-liner (max 15 words) that captures the essence of this news. Be concise and impactful."""),
            ("user", "{title}")
        ])
        
        chain = prompt | self.llm | self.str_parser
        
        try:
            result = await chain.ainvoke({"title": title})
            return result.strip()
        except Exception as e:
            print(f"Error generating one-liner: {e}")
            return title

    async def generate_catchy_summary(self, item: NewsItem) -> str:
        """Generate a catchy summary for the main story"""
        date_context = get_current_date_context()
        current_year = datetime.now().year
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

You are a copywriter creating engaging newsletter summaries in {current_year}.

Write a 2-3 sentence summary that:
1. Hooks the reader immediately
2. Explains the key point
3. Creates urgency or curiosity
4. Uses active voice
5. Ends with a hook or question

IMPORTANT: We are in {current_year}. Do NOT reference 2024 or past years as current."""),
            ("user", "Create a catchy summary for:\n\nTitle: {{title}}\nOriginal Summary: {{summary}}")
        ])
        
        chain = prompt | self.llm | self.str_parser
        
        try:
            result = await chain.ainvoke({
                "title": item.title,
                "summary": item.summary or "No summary provided"
            })
            return result.strip()
        except Exception as e:
            print(f"Error generating catchy summary: {e}")
            return item.summary
