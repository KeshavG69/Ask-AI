"""
🚀 STREAMING BEAST - Backend Stream Processor
Transforms complex agno streams into clean, simple chunks for lightning-fast frontend consumption!
"""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from agno.run.response import RunResponse, RunEvent
import logging

logger = logging.getLogger(__name__)


class StreamProcessor:
    """
    🔥 THE STREAMING MONSTER
    Processes complex agno streams and emits clean, simple chunks for frontend
    """

    def __init__(self):
        self.reasoning_steps = []
        self.content_buffer = ""
        self.crawled_urls = []
        self.is_streaming = False

    async def process_stream(
        self, raw_stream: AsyncGenerator
    ) -> AsyncGenerator[str, None]:
        """
        🚀 MAIN PROCESSING ENGINE
        Takes raw agno stream, processes complex logic, emits clean chunks
        """
        try:
            logger.info("🔥 Stream processor activated!")

            async for run_response_chunk in raw_stream:
                # Handle the raw stream object directly - no conversion needed!
                async for clean_chunk in self._process_chunk(run_response_chunk):
                    yield f"data: {json.dumps(clean_chunk)}\n\n"

            logger.info("✅ Stream processing completed!")

        except Exception as e:
            logger.error(f"❌ Stream processor error: {str(e)}")
            error_chunk = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_chunk)}\n\n"

    async def _process_chunk(
        self, chunk: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        🧠 CHUNK PROCESSING BRAIN  
        Analyzes each chunk and emits appropriate clean data
        """
        
        # DEBUG: Log what we're receiving
        logger.info(f"🔍 Processing chunk: {type(chunk)} - {getattr(chunk, 'event', 'NO_EVENT')}")
        
        # Get event type safely 
        event = getattr(chunk, 'event', None)
        
        # Stream start
        if event == RunEvent.run_started:
            self._reset_state()
            yield {"type": "stream_start", "message": "Starting response..."}

        # Content streaming - THE MONEY SHOT! 🎯
        elif event == RunEvent.run_response_content:
            content = getattr(chunk, 'content', None)
            if content and isinstance(content, str):
                self.content_buffer += content
                self.is_streaming = True

                yield {
                    "type": "content",
                    "text": content,  # Individual chunk for real-time streaming
                    "full_content": self.content_buffer,  # Full content so far
                }

        # Tool calls - Reasoning extraction 🧠
        elif event == RunEvent.tool_call_started:
            tool = getattr(chunk, 'tool', None)
            if tool and hasattr(tool, "tool_name"):

                # Crawling detection
                if tool.tool_name == "crawl_selected_urls":
                    if hasattr(tool, "tool_args") and tool.tool_args:
                        urls = tool.tool_args.get("urls", [])
                        self.crawled_urls.extend(urls)

                        yield {
                            "type": "crawling",
                            "urls": urls,
                            "message": f"Analyzing {len(urls)} pages...",
                        }

                # Reasoning extraction
                elif tool.tool_name == "think":
                    if hasattr(tool, "tool_args") and tool.tool_args:
                        reasoning_step = {
                            "title": tool.tool_args.get("title", "Thinking..."),
                            "thought": tool.tool_args.get("thought", ""),
                            "confidence": tool.tool_args.get("confidence", 1.0),
                        }

                        self.reasoning_steps.append(reasoning_step)

                        yield {
                            "type": "reasoning",
                            "step": reasoning_step,
                            "all_steps": self.reasoning_steps,
                        }

        # Stream completion - Final package 📦
        elif event == RunEvent.run_completed:
            self.is_streaming = False

            # Final content if provided
            content = getattr(chunk, 'content', None)
            if content and isinstance(content, str):
                self.content_buffer = content

            # Process sources from crawled URLs
            sources = self._process_sources(self.crawled_urls)

            yield {
                "type": "completion",
                "final_content": self.content_buffer,
                "reasoning_steps": self.reasoning_steps,
                "sources": sources,
                "crawled_urls": self.crawled_urls,
            }

        # Error handling  
        elif event == RunEvent.run_error:
            content = getattr(chunk, 'content', None)
            yield {"type": "error", "message": content or "An error occurred"}
            
        # FALLBACK - If we don't recognize the event, at least yield something
        else:
            logger.warning(f"⚠️ Unhandled event type: {event}")
            yield {"type": "debug", "event": str(event), "data": str(chunk)}

    def _process_sources(self, urls: List[str]) -> List[Dict[str, str]]:
        """
        🔗 SOURCE PROCESSOR
        Converts URLs into clean source objects
        """
        sources = []
        for url in urls:
            try:
                from urllib.parse import urlparse

                parsed = urlparse(url)
                sources.append(
                    {
                        "url": url,
                        "domain": parsed.hostname or "Unknown",
                        "title": url.split("/")[-1]
                        or parsed.pathname.split("/")[-1]
                        or "Documentation",
                    }
                )
            except:
                sources.append({"url": url, "domain": "Unknown", "title": url})

        return sources

    def _reset_state(self):
        """Reset processor state for new stream"""
        self.reasoning_steps = []
        self.content_buffer = ""
        self.crawled_urls = []
        self.is_streaming = False


# 🚀 GLOBAL PROCESSOR INSTANCE
stream_processor = StreamProcessor()


async def process_agent_stream(raw_stream: AsyncGenerator) -> AsyncGenerator[str, None]:
    """
    🎯 MAIN ENTRY POINT
    Process raw agno stream into clean chunks
    """
    async for processed_chunk in stream_processor.process_stream(raw_stream):
        yield processed_chunk
