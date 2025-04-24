import logging
import json
import os
from typing import Dict, Any, List, Optional
import re
from bs4 import BeautifulSoup
import requests
from datetime import datetime

from src.utils.config import get_config
from src.utils.database import Session, Pin

logger = logging.getLogger(__name__)


class ContentGenerator:
    """Content generation and optimization"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or get_config()
        self.api_key = self.config.get("OPENAI_API_KEY")
        self.model = self.config.get("OPENAI_MODEL", "gpt-3.5-turbo")

    def generate_article(
        self, topic: str, keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Generate an SEO-optimized article"""
        try:
            # Prepare prompt
            prompt = self._create_article_prompt(topic, keywords)

            # Generate content
            content = self._generate_content(prompt)

            # Optimize for SEO
            optimized_content = self._optimize_for_seo(content, keywords)

            return {
                "title": optimized_content["title"],
                "content": optimized_content["content"],
                "meta_description": optimized_content["meta_description"],
                "keywords": keywords or [],
            }

        except Exception as e:
            logger.error(f"Error generating article: {e}")
            raise

    def generate_images(self, description: str, count: int = 1) -> List[str]:
        """Generate images using free service"""
        try:
            # This is a placeholder for actual image generation
            # In a real implementation, you would call an image generation API
            return [f"https://example.com/image_{i}.jpg" for i in range(count)]

        except Exception as e:
            logger.error(f"Error generating images: {e}")
            raise

    def _create_article_prompt(self, topic: str, keywords: List[str] = None) -> str:
        """Create a prompt for article generation"""
        prompt = f"""
        Write a comprehensive article about {topic}.
        
        Requirements:
        - Length: 1000-1500 words
        - Include proper HTML structure (H1, H2, H3 tags)
        - Natural keyword integration
        - Engaging introduction and conclusion
        - Clear sections and subsections
        - SEO-friendly meta description
        
        Keywords to include: {', '.join(keywords or [])}
        """
        return prompt

    def _generate_content(self, prompt: str) -> str:
        """Generate content using AI model"""
        try:
            # Get model from config
            model = self.config.get("model", "gpt-3.5-turbo")

            # Prepare headers based on model
            if "gemini" in model.lower():
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-Model": model,
                }
            else:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

            # Prepare request data
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000,
            }

            # Make API request
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"API request failed: {response.text}")
                raise Exception(f"API request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise

    def _optimize_for_seo(
        self, content: str, keywords: List[str] = None
    ) -> Dict[str, str]:
        """Optimize content for SEO"""
        try:
            # Parse HTML
            soup = BeautifulSoup(content, "html.parser")

            # Extract title
            title = soup.find("h1").text if soup.find("h1") else "Default Title"

            # Generate meta description
            meta_description = self._generate_meta_description(content)

            # Optimize content
            optimized_content = self._optimize_content(content, keywords)

            return {
                "title": title,
                "content": optimized_content,
                "meta_description": meta_description,
            }

        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            raise

    def _generate_meta_description(self, content: str, max_length: int = 160) -> str:
        """Generate meta description"""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", content)

        # Get first paragraph
        first_para = text.split("\n")[0]

        # Truncate to max length
        if len(first_para) > max_length:
            first_para = first_para[: max_length - 3] + "..."

        return first_para

    def _optimize_content(self, content: str, keywords: List[str] = None) -> str:
        """Optimize content with keywords"""
        if not keywords:
            return content

        # Add keywords naturally
        for keyword in keywords:
            if keyword.lower() not in content.lower():
                # Find a good place to add the keyword
                content = self._add_keyword_naturally(content, keyword)

        return content

    def _add_keyword_naturally(self, content: str, keyword: str) -> str:
        """Add keyword naturally to content"""
        # This is a simple implementation
        # In a real implementation, you would use NLP to find the best place
        paragraphs = content.split("\n")
        if len(paragraphs) > 1:
            # Add to second paragraph
            paragraphs[1] = f"{keyword} is an important aspect. {paragraphs[1]}"
        return "\n".join(paragraphs)
