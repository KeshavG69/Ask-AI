"""
🚀 SIMPLE STREAM PROCESSOR - GET THE BANANAS! 
Minimal processor to test streaming works
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any
from agno.run.response import RunResponse, RunEvent

logger = logging.getLogger(__name__)

async def simple_process_stream(raw_stream: AsyncGenerator) -> AsyncGenerator[str, None]:
    """
    🍌 BANANA PROCESSOR - Now with REAL CONTENT EXTRACTION + NO REPETITION!
    """
    try:
        logger.info("🍌 BANANA PROCESSOR ACTIVATED - EXTRACTING REAL CONTENT!")
        
        content_buffer = ""
        reasoning_steps = []
        sent_reasoning_steps = []  # Track what we've already sent to prevent repetition
        crawled_urls = []
        
        async for chunk in raw_stream:
            event = getattr(chunk, 'event', None)
            # logger.info(f"🔍 Processing: {event}")
            
            # 🎯 CONTENT STREAMING - THE MONEY SHOT!
            if event == RunEvent.run_response_content:
                content = getattr(chunk, 'content', None)
                if content and isinstance(content, str):
                    content_buffer += content
                    
                    yield f"data: {json.dumps({
                        'type': 'content',
                        'text': content,
                        'full_content': content_buffer
                    })}\n\n"
            
            # 🧠 REASONING EXTRACTION
            elif event == RunEvent.tool_call_started:
                tool = getattr(chunk, 'tool', None)
                if tool and hasattr(tool, 'tool_name'):
                    
                    # Crawling detection
                    if tool.tool_name == 'crawl_selected_urls':
                        if hasattr(tool, 'tool_args') and tool.tool_args:
                            urls = tool.tool_args.get('urls', [])
                            crawled_urls.extend(urls)
                            
                            yield f"data: {json.dumps({
                                'type': 'crawling',
                                'urls': urls,
                                'message': f'Analyzing {len(urls)} pages...'
                            })}\n\n"
                    
                    # Reasoning steps - ONLY SEND NEW STEPS!
                    elif tool.tool_name == 'think':
                        if hasattr(tool, 'tool_args') and tool.tool_args:
                            reasoning_step = {
                                'title': tool.tool_args.get('title', 'Thinking...'),
                                'thought': tool.tool_args.get('thought', ''),
                                'confidence': tool.tool_args.get('confidence', 1.0)
                            }
                            
                            # Check if this is a NEW step we haven't sent before
                            step_key = f"{reasoning_step['title']}:{reasoning_step['thought']}"
                            if step_key not in sent_reasoning_steps:
                                reasoning_steps.append(reasoning_step)
                                sent_reasoning_steps.append(step_key)
                                
                                # 🎯 ONLY SEND THE NEW STEP - NO REPETITION!
                                yield f"data: {json.dumps({
                                    'type': 'reasoning',
                                    'step': reasoning_step,
                                    'step_number': len(reasoning_steps),
                                    'is_new': True
                                })}\n\n"
                                
                                logger.info(f"🧠 NEW reasoning step sent: {reasoning_step['title']}")
                            else:
                                logger.info(f"🔄 Skipping duplicate reasoning step: {reasoning_step['title']}")
            
            # 📦 COMPLETION - FINAL PACKAGE
            elif event == RunEvent.run_completed:
                # Final content if provided
                final_content = getattr(chunk, 'content', None)
                if final_content and isinstance(final_content, str):
                    content_buffer = final_content
                
                # Process sources
                sources = []
                for url in crawled_urls:
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        sources.append({
                            'url': url,
                            'domain': parsed.hostname or 'Unknown',
                            'title': url.split('/')[-1] or 'Documentation'
                        })
                    except:
                        sources.append({
                            'url': url,
                            'domain': 'Unknown',
                            'title': url
                        })
                
                yield f"data: {json.dumps({
                    'type': 'completion',
                    'final_content': content_buffer,
                    'sources': sources,
                    'crawled_urls': crawled_urls
                })}\n\n"
            
            # 🚨 ERROR HANDLING
            elif event == RunEvent.run_error:
                error_content = getattr(chunk, 'content', None)
                yield f"data: {json.dumps({
                    'type': 'error',
                    'message': error_content or 'An error occurred'
                })}\n\n"
            
        logger.info("🍌 BANANA PROCESSING COMPLETED!")
        
    except Exception as e:
        logger.error(f"❌ Banana processor error: {str(e)}")
        error_chunk = {"type": "error", "message": str(e)}
        yield f"data: {json.dumps(error_chunk)}\n\n"
