"""
AI Service using LangChain for newsletter content generation
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import json

from app.config import settings


def get_current_date_context() -> str:
    """Get current date context string for prompts"""
    now = datetime.now()
    return f"CURRENT DATE: {now.strftime('%B %d, %Y')} (Year: {now.year}). All content should be relevant to {now.year}, not past years."


# Output schemas for structured responses
class NewsImpactOutput(BaseModel):
    whyItMatters: str = Field(description="Why this news matters to business owners")
    actionItems: List[str] = Field(description="Action items for business owners")


class HookTitleOutput(BaseModel):
    title: str = Field(description="Catchy hook-style title")


class StoryOutput(BaseModel):
    story: str = Field(description="Full story content in 400-500 words")


class OneLinerOutput(BaseModel):
    text: str = Field(description="One-liner summary")


class AIService:
    def __init__(self):
        # Using gpt-4.1-mini for production - optimal balance of speed, cost, and quality
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        self.str_parser = StrOutputParser()
        self.json_parser = JsonOutputParser()
    
    async def generate_hook_title(self, original_title: str) -> str:
        """Generate a catchy hook-style title using LangChain"""
        date_context = get_current_date_context()
        prompt = ChatPromptTemplate.from_messages([
             ("system", f"""{date_context}

You are an expert newsletter headline writer. Transform headlines into compelling, click-worthy titles that sound natural and human-written.

RULES:
- Keep it under 10 words
- Use power words, numbers, or intriguing questions
- Make it conversational and punchy
- Reference {datetime.now().year} if mentioning dates
- Avoid clichés like "game-changer" or "revolutionary"
- NO em dashes (—), NO colons in the middle, NO unnecessary punctuation
- Sound like a real person wrote it, not AI

Return ONLY the rewritten headline."""),
            ("user", "Rewrite this headline:\n\n{title}")
        ])
        chain = prompt | self.llm | self.str_parser
        result = await chain.ainvoke({"title": original_title})
        return result.strip().strip('"')

    async def generate_description(self, title: str) -> str:
        """Generate a compelling description/intro for the newsletter"""
        date_context = get_current_date_context()
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

You are writing the opening hook for a digital marketing newsletter. Create a compelling 1-2 sentence description that makes readers want to keep reading.

STYLE:
- Write like a human, not a robot
- Be specific and intriguing
- Use simple, direct language
- Keep sentences short and punchy
- Under 25 words total
- NO em dashes (—), NO semicolons, NO overly formal language
- NO phrases like: "delve into," "in today's landscape," "furthermore," "moreover"

Just write the description naturally."""),
            ("user", "Write a compelling intro for this newsletter topic:\n\n{title}")
        ])
        
        chain = prompt | self.llm | self.str_parser
        result = await chain.ainvoke({"title": title})
        return result.strip()

    async def generate_summary(self, title: str, existing_summary: Optional[str] = None) -> str:
        """Generate a comprehensive summary (150-200 words) from news title and content"""
        date_context = get_current_date_context()
        current_year = datetime.now().year
        
        # Build context from title and any existing content
        news_context = f"Title: {title}"
        if existing_summary and len(existing_summary.strip()) > 10:
            news_context += f"\n\nOriginal Content/Context: {existing_summary}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

You are a digital marketing journalist writing a newsletter summary. Write 150-200 words that inform and engage readers.

WRITING STYLE:
- Write like a knowledgeable human, not AI
- Use short sentences (10-20 words each)
- Be conversational but professional
- Vary sentence structure naturally
- Start some sentences with context or transition words naturally
- No need to add title in starting
FORBIDDEN PHRASES/STYLE:
- ABSOLUTELY FORBIDDEN: NO em dashes (—) or en dashes (–) anywhere - USE COMMAS OR PERIODS INSTEAD
- NO semicolons
- NO phrases like: "delve into," "dive into," "in today's landscape," "it's worth noting," "furthermore," "moreover," "additionally," "however" at sentence starts
- NO overuse of "also," "as well," "in fact"
- NO corporate buzzwords: "ecosystem," "synergy," "leverage," "robust," "seamlessly"

CRITICAL: If you need to connect ideas, use commas, periods, or the word "and". NEVER use em dashes (—) or en dashes (–).

MARKDOWN FORMATTING:
- Use **bold** for 3-4 key terms or phrases only
- Use natural paragraph breaks (leave a blank line between paragraphs)
- Write in 2-3 short paragraphs
- First paragraph: introduce the news clearly
- Second paragraph: explain what it means and why it matters
- Third paragraph (if needed): provide context or specific examples

CONTENT REQUIREMENTS:
- Word count: EXACTLY 150-200 words (critical!)
- Focus on {current_year} - DO NOT mention 2024 or past years as current
- Include specific details, data, or examples where possible
- Explain the business impact for digital marketers
- Sound authoritative but accessible

Write naturally as if explaining to a colleague over coffee."""),
            ("user", f"Write a 150-200 word summary with proper markdown formatting:\n\n{news_context}")
        ])
        
        chain = prompt | self.llm | self.str_parser
        result = await chain.ainvoke({})
        # Post-process to remove any em dashes that might have slipped through
        result = result.replace('—', ',').replace('–', '-').strip()
        return result

    async def generate_main_article(self, title: str, summary: str = "", word_count: int = 300) -> str:
        """Generate the main article with customizable word count (default 250-350 words for main article)"""
        date_context = get_current_date_context()
        current_year = datetime.now().year
        
        # Calculate word range based on word_count parameter
        min_words = max(50, word_count - 50)
        max_words = word_count + 50
        
        # Build the content directly in the prompt
        article_context = f"Title: {title}\nContext: {summary or 'No additional context'}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

You are a digital marketing thought leader writing the main feature for a prestigious newsletter. Write {min_words}-{max_words} words that sound expertly crafted but naturally human.

WRITING STYLE:
- Write like a seasoned industry expert
- Mix short punchy sentences with flowing explanations
- Be confident and insightful, not generic
- Use specific examples over vague statements
- Sound conversational yet authoritative
- Vary sentence length and structure naturally

FORBIDDEN PHRASES/STYLE:
- ABSOLUTELY FORBIDDEN: NO em dashes (—) or en dashes (–) anywhere - USE COMMAS OR PERIODS INSTEAD
- NO semicolons
- NO overused AI transitions: "furthermore," "moreover," "however" starting sentences
- NO clichés: "game-changer," "revolutionary," "cutting-edge," "delve into," "in today's landscape"
- NO corporate buzzwords: "ecosystem," "synergy," "leverage," "seamlessly," "robust," "holistic"
- NO generic filler sentences that say nothing specific

CRITICAL: If you need to connect ideas, use commas, periods, or the word "and". NEVER use em dashes (—) or en dashes (–).

MARKDOWN FORMATTING:
- Use **bold** for 4-6 key terms/phrases (don't overdo it)
- Use ### for "Key Takeaways" section heading only
- Break into 4-5 short paragraphs (2-4 sentences each)
- Leave blank lines between paragraphs
- Use bullet points (- ) ONLY for the takeaways section (2-3 bullets)
- Each bullet should start with an action verb and be specific

STRUCTURE:
1. **Opening** (2-3 sentences): Compelling hook about the topic's significance
2. **Context & Analysis** (2 paragraphs): Deep insights with specifics about {current_year} trends
3. **### Key Takeaways** (2-3 bullet points): Actionable advice starting with verbs
4. **Closing** (1-2 sentences): Forward-looking statement or powerful conclusion

CONTENT REQUIREMENTS:
- Word count: {min_words}-{max_words} words (CRITICAL - stay within this range!)
- Reference {current_year} trends and data
- Include specific numbers or examples where possible
- Make it actionable - readers should learn something valuable
- Sound authoritative but not stuffy
- Use "you" to speak directly to readers occasionally

Write as if you're the industry expert everyone turns to for insights."""),
            ("user", f"Write a polished {min_words}-{max_words} word feature article with markdown:\n\n{article_context}")
        ])
        
        chain = prompt | self.llm | self.str_parser
        result = await chain.ainvoke({})
        # Post-process to remove any em dashes that might have slipped through
        result = result.replace('—', ',').replace('–', '-').strip()
        return result

    async def generate_one_liner(self, title: str) -> str:
        """Generate a one-liner summary for Trendsetter/Top News sections"""
        date_context = get_current_date_context()
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

You are a newsletter editor writing punchy one-liners. Write a concise summary (max 15 words) that captures the essence of this news.

STYLE:
- Direct and impactful
- Conversational but professional
- NO unnecessary words or fluff
- NO em dashes, NO colons, NO complex punctuation
- Just state the key point clearly

Write like you're texting a colleague the most important detail."""),
            ("user", "Write a one-liner for:\n\n{title}")
        ])
        
        chain = prompt | self.llm | self.str_parser
        result = await chain.ainvoke({"title": title})
        # Post-process to remove any em dashes that might have slipped through
        result = result.replace('—', ',').replace('–', '-').strip()
        return result

    async def generate_editor_note(self, content: str, max_words: int = 180, paragraphs: int = 3) -> str:
        """Generate a 'Notes from the Editor' section based on newsletter content"""
        date_context = get_current_date_context()
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

You are Victor Huynh, Director at ReadyArtwork, writing a personal note to your newsletter readers.

Write a warm, engaging "Notes from the Editor" that sounds authentically human and personal.

WRITING STYLE:
- Write like you're emailing a friend in your industry
- Be warm, approachable, and genuine
- Mix short and medium sentences naturally
- Share your actual perspective, not generic observations
- Use "I" and "we" - make it personal
- Show personality while staying professional

CRITICAL PUNCTUATION RULES:
- ABSOLUTELY NO em dashes (—) anywhere in your writing - USE A COMMA OR PERIOD INSTEAD
- ABSOLUTELY NO en dashes (–) either
- NO semicolons
- Use commas, periods, or the word "and" to connect ideas
- Use simple punctuation only: periods, commas, question marks, exclamation points

FORBIDDEN PHRASES/STYLE:
- NO corporate speak: "delve," "leverage," "ecosystem," "seamlessly"
- NO overused transitions: "furthermore," "moreover," "in addition"
- NO generic observations that could apply to any newsletter

STRUCTURE:
- Write EXACTLY {paragraphs} paragraphs
- Maximum {max_words} words total to 200 words strict.
- Paragraph 1: Open with a personal observation or hook about this week's themes
- Paragraph 2: Connect the stories to what you're seeing in the industry
- Paragraph 3: Close with why this matters or what you're watching next
- Leave blank lines between paragraphs

CONTENT:
- Reference specific stories from the newsletter naturally
- Share your genuine perspective on trends
- Make it feel like insider insights from someone in the know
- End on a forward-looking or thoughtful note

FINAL REMINDER: Do NOT use em dashes (—) or en dashes (–). Use commas or periods instead.

Write like Victor actually sat down and wrote this - personal, insightful, and real."""),
            ("user", "Write a 'Notes from the Editor' based on this newsletter content:\n\n{content}")
        ])
        
        chain = prompt | self.llm | self.str_parser
        result = await chain.ainvoke({"content": content})
        # Post-process to remove any em dashes that might have slipped through
        result = result.replace('—', ',').replace('–', '-').strip()
        return result

    async def generate_news_impact(
        self,
        title: str,
        description: str,
        source: str,
        category: str
    ) -> Dict[str, any]:
        """Generate business impact analysis for a news article"""
        date_context = get_current_date_context()
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{date_context}

You are a digital marketing consultant analyzing news for business owners. Be specific and actionable.

WRITING STYLE:
- Write clearly and directly
- Be specific, not vague
- Use simple language
- NO em dashes, NO jargon, NO filler
- Focus on real business impact

Provide valid JSON with:
1. "whyItMatters": 1-2 specific sentences on business impact (not generic)
2. "actionItems": Array of 1-2 concrete actions (start with action verbs)

Total under 80 words. Be specific and useful."""),
            ("user", """News Article:
Title: {title}
Description: {description}
Source: {source}
Category: {category}

Analyze the business impact:""")
        ])
        
        chain = prompt | self.llm | self.json_parser
        
        try:
            result = await chain.ainvoke({
                "title": title,
                "description": description,
                "source": source,
                "category": category
            })
            
            return {
                "whyItMatters": result.get("whyItMatters", ""),
                "actionItems": result.get("actionItems", []),
                "tokens_used": 0
            }
        except Exception as e:
            print(f"Error parsing impact JSON: {e}")
            return {
                "whyItMatters": "Unable to generate impact analysis.",
                "actionItems": ["Please try again."],
                "tokens_used": 0
            }

    async def rewrite_title(self, title: str) -> str:
        """Alias for generate_hook_title for backward compatibility"""
        return await self.generate_hook_title(title)
