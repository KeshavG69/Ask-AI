import logging
import os
from fastapi import HTTPException
from openai import OpenAI
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)


class ContentModerator:
    """Utility class for content moderation using OpenAI's Moderation API."""

    def __init__(self, api_key=None):
        """Initialize with API key from environment if not provided."""
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    async def check_content(
        self,
        content: str,
        model: str = "omni-moderation-latest",
        return_scores: bool = False,
    ) -> Union[Dict[str, Any], bool]:
        """
        Check if content is appropriate using OpenAI's Moderation API.

        Args:
            content (str): Text content to check
            model (str): OpenAI moderation model to use
            return_scores (bool): Whether to return full moderation details or just a boolean

        Returns:
            If return_scores=True: Dict with moderation results
            If return_scores=False: Boolean (True if content is appropriate, False if flagged)
        """
        if not content or not content.strip():
            # Empty content is considered safe
            return True if not return_scores else {"flagged": False}

        try:
            logger.info(f"🔍 Checking content moderation for query: {content[:50]}...")

            response = self.client.moderations.create(model=model, input=content)

            result = response.results[0]

            logger.info(f"📋 Moderation result: flagged={result.flagged}")

            # If only need boolean result
            if not return_scores:
                return not result.flagged

            # Return full results
            return {
                "flagged": result.flagged,
                "categories": result.categories.model_dump(),
                "category_scores": result.category_scores.model_dump(),
            }

        except Exception as e:
            logger.error(f"❌ Content moderation failed: {e}")
            # In case of error, default to allowing content (fail open)
            return True if not return_scores else {"flagged": False, "error": str(e)}

    def is_content_appropriate(self, content: str) -> bool:
        """
        Synchronous wrapper to check if content is appropriate.

        Args:
            content (str): Text content to check

        Returns:
            bool: True if content is appropriate, False if flagged
        """
        import asyncio

        # Handle event loop for synchronous calls
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to handle this differently
                return asyncio.create_task(self.check_content(content)).result()
            else:
                return loop.run_until_complete(self.check_content(content))
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.check_content(content))
            finally:
                loop.close()


# Singleton instance
_content_moderator = ContentModerator()
