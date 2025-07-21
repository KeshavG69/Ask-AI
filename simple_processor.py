"""
🚀 SIMPLE STREAM PROCESSOR - GET THE BANANAS!
Minimal processor to test streaming works
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any
from agno.run.response import RunResponse, RunEvent

logger = logging.getLogger(__name__)


async def simple_process_stream(
    raw_stream: AsyncGenerator,
) -> AsyncGenerator[str, None]:
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
            event = getattr(chunk, "event", None)
            # logger.info(f"🔍 Processing: {event}")

            # 🎯 CONTENT STREAMING - THE MONEY SHOT!
            if event == RunEvent.run_response_content:
                content = getattr(chunk, "content", None)
                if content and isinstance(content, str):
                    content_buffer += content

                    yield (
    f"data: {json.dumps({ 
        'type': 'content',
        'text': content,
        'full_content': content_buffer
    })}\n\n"
)



            # 🧠 REASONING EXTRACTION WITH ENHANCED DEBUG
            elif event == RunEvent.tool_call_started:
                tool = getattr(chunk, "tool", None)
                logger.info(
                    f"🔍 [TOOL_CALL_STARTED] Tool: {tool.tool_name if tool and hasattr(tool, 'tool_name') else 'None'}"
                )

                if tool and hasattr(tool, "tool_name"):

                    # Crawling detection - handle both crawler and Exa tools
                    if tool.tool_name == "crawl_selected_urls":
                        if hasattr(tool, "tool_args") and tool.tool_args:
                            urls = tool.tool_args.get("urls", [])
                            crawled_urls.extend(urls)

                            yield f"data: {json.dumps({
                                'type': 'crawling',
                                'urls': urls,
                                'message': f'Analyzing {len(urls)} pages...'
                            })}\n\n"
                    
                    # Exa search detection - just show search message, URLs come from result
                    elif tool.tool_name in ["get_contents", "search", "exa_search", "search_exa"]:
                        yield f"data: {json.dumps({
                            'type': 'crawling',
                            'urls': [],
                            'message': 'Searching the web...'
                        })}\n\n"

                    # Reasoning steps - HANDLE BOTH THINK AND ANALYZE TOOLS
                    elif tool.tool_name in ["think", "analyze"]:
                        logger.info(
                            f"🧠 [REASONING DETECTED] Processing {tool.tool_name} tool"
                        )

                        if hasattr(tool, "tool_args") and tool.tool_args:
                            # Handle different argument structures for think vs analyze tools
                            if tool.tool_name == "think":
                                reasoning_step = {
                                    "title": tool.tool_args.get("title", "Thinking..."),
                                    "thought": tool.tool_args.get("thought", ""),
                                    "confidence": tool.tool_args.get("confidence", 1.0),
                                }
                            elif tool.tool_name == "analyze":
                                reasoning_step = {
                                    "title": tool.tool_args.get(
                                        "title", "Analyzing..."
                                    ),
                                    "thought": tool.tool_args.get(
                                        "result", ""
                                    ),  # analyze uses 'result' instead of 'thought'
                                    "confidence": tool.tool_args.get("confidence", 1.0),
                                }
                            else:
                                reasoning_step = {
                                    "title": tool.tool_args.get(
                                        "title", "Processing..."
                                    ),
                                    "thought": tool.tool_args.get(
                                        "thought", tool.tool_args.get("result", "")
                                    ),
                                    "confidence": tool.tool_args.get("confidence", 1.0),
                                }

                            logger.info(
                                f"🧠 [REASONING STEP] Title: {reasoning_step['title']}"
                            )
                            logger.info(
                                f"🧠 [REASONING STEP] Thought length: {len(reasoning_step['thought'])} chars"
                            )
                            logger.info(
                                f"🧠 [REASONING STEP] Current total steps: {len(reasoning_steps)}"
                            )

                            # Create a simpler step key for duplicate detection
                            step_key = reasoning_step["title"]
                            logger.info(f"🧠 [DUPLICATE CHECK] Step key: {step_key}")
                            logger.info(
                                f"🧠 [DUPLICATE CHECK] Previously sent steps: {sent_reasoning_steps}"
                            )

                            if step_key not in sent_reasoning_steps:
                                reasoning_steps.append(reasoning_step)
                                sent_reasoning_steps.append(step_key)

                                # 🎯 SEND THE NEW STEP!
                                reasoning_chunk = {
                                    "type": "reasoning",
                                    "step": reasoning_step,
                                    "step_number": len(reasoning_steps),
                                    "is_new": True,
                                }

                                yield f"data: {json.dumps(reasoning_chunk)}\n\n"

                                logger.info(
                                    f"✅ [REASONING SENT] Step #{len(reasoning_steps)}: {reasoning_step['title']}"
                                )
                            else:
                                logger.warning(
                                    f"⚠️ [DUPLICATE SKIPPED] Step already sent: {reasoning_step['title']}"
                                )
                        else:
                            logger.warning(
                                f"⚠️ [REASONING ERROR] Think tool missing args: {tool}"
                            )
                    else:
                        logger.info(f"🔧 [OTHER TOOL] Tool name: {tool.tool_name}")
                else:
                    logger.warning(f"⚠️ [TOOL ERROR] Invalid tool object: {tool}")

            # 🔍 TOOL CALL COMPLETED - Extract URLs from Exa search results
            elif event == RunEvent.tool_call_completed:
                tool = getattr(chunk, "tool", None)
                logger.info(
                    f"🔍 [TOOL_CALL_COMPLETED] Tool: {tool.tool_name if tool and hasattr(tool, 'tool_name') else 'None'}"
                )
                
                if tool and hasattr(tool, "tool_name") and tool.tool_name in ["search_exa", "exa_search", "get_contents"]:
                    # Extract URLs from Exa search results
                    result = getattr(tool, "result", None)
                    if result:
                        try:
                            import json as json_lib
                            # Parse the result if it's a JSON string
                            if isinstance(result, str):
                                exa_data = json_lib.loads(result)
                            else:
                                exa_data = result
                            
                            if isinstance(exa_data, list):
                                extracted_urls = []
                                for item in exa_data:
                                    if isinstance(item, dict) and 'url' in item:
                                        extracted_urls.append(item['url'])
                                        crawled_urls.append(item['url'])
                                
                                if extracted_urls:
                                    logger.info(f"🔍 Extracted {len(extracted_urls)} URLs from Exa search result")
                                    # Send crawling update with actual URLs
                                    yield f"data: {json.dumps({
                                        'type': 'crawling',
                                        'urls': extracted_urls,
                                        'message': f'Found {len(extracted_urls)} relevant sources...'
                                    })}\n\n"
                                    
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to extract URLs from Exa result: {e}")

            # 📦 COMPLETION - FINAL PACKAGE
            elif event == RunEvent.run_completed:
                # Final content if provided
                final_content = getattr(chunk, "content", None)
                if final_content and isinstance(final_content, str):
                    content_buffer = final_content

                # Process sources - handle both crawler URLs and Exa search results
                sources = []
                
                # Extract URLs from Exa search results if present in content
                try:
                    # Look for Exa search results in content buffer - more robust JSON extraction
                    if content_buffer and ('"url":' in content_buffer or "'url':" in content_buffer):
                        # Try multiple patterns to find JSON arrays with URL objects
                        import re
                        import json as json_lib
                        
                        # Pattern 1: Complete JSON array
                        json_pattern = r'\[\s*{[^}]*"url"[^}]*}[^]]*\]'
                        json_matches = re.findall(json_pattern, content_buffer, re.DOTALL)
                        
                        for json_str in json_matches:
                            try:
                                exa_data = json_lib.loads(json_str)
                                if isinstance(exa_data, list):
                                    logger.info(f"🔍 Found Exa search results: {len(exa_data)} items")
                                    for item in exa_data:
                                        if isinstance(item, dict) and 'url' in item:
                                            from urllib.parse import urlparse
                                            parsed = urlparse(item['url'])
                                            sources.append({
                                                "url": item['url'],
                                                "domain": parsed.hostname or "Unknown",
                                                "title": item.get('title', item['url'].split('/')[-1] or "Search Result"),
                                            })
                                            crawled_urls.append(item['url'])  # Add to crawled_urls too
                            except Exception as parse_error:
                                logger.warning(f"⚠️ Failed to parse Exa JSON: {parse_error}")
                                continue
                        
                        # Pattern 2: Individual URL extraction as fallback
                        if not json_matches:
                            url_pattern = r'"url":\s*"([^"]+)"'
                            url_matches = re.findall(url_pattern, content_buffer)
                            title_pattern = r'"title":\s*"([^"]+)"'
                            title_matches = re.findall(title_pattern, content_buffer)
                            
                            for i, url in enumerate(url_matches):
                                from urllib.parse import urlparse
                                parsed = urlparse(url)
                                title = title_matches[i] if i < len(title_matches) else url.split('/')[-1] or "Search Result"
                                sources.append({
                                    "url": url,
                                    "domain": parsed.hostname or "Unknown", 
                                    "title": title,
                                })
                                crawled_urls.append(url)
                                
                            if url_matches:
                                logger.info(f"🔍 Extracted {len(url_matches)} URLs from Exa results (fallback method)")
                                
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract Exa URLs: {e}")
                
                # Add regular crawler URLs as sources (avoid duplicates)
                existing_urls = {source['url'] for source in sources}
                for url in crawled_urls:
                    if url not in existing_urls:
                        try:
                            from urllib.parse import urlparse
                            parsed = urlparse(url)
                            sources.append(
                                {
                                    "url": url,
                                    "domain": parsed.hostname or "Unknown",
                                    "title": url.split("/")[-1] or "Documentation",
                                }
                            )
                        except:
                            sources.append({"url": url, "domain": "Unknown", "title": url})

                # Remove duplicate sources by URL
                unique_sources = []
                seen_urls = set()
                for source in sources:
                    if source['url'] not in seen_urls:
                        unique_sources.append(source)
                        seen_urls.add(source['url'])

                yield f"data: {json.dumps({
                    'type': 'completion',
                    'final_content': content_buffer,
                    'sources': unique_sources,
                    'crawled_urls': list(set(crawled_urls))  # Remove duplicates from crawled_urls too
                })}\n\n"

            # 🚨 ERROR HANDLING
            elif event == RunEvent.run_error:
                error_content = getattr(chunk, "content", None)
                yield f"data: {json.dumps({
                    'type': 'error',
                    'message': error_content or 'An error occurred'
                })}\n\n"

        logger.info("🍌 BANANA PROCESSING COMPLETED!")

    except Exception as e:
        logger.error(f"❌ Banana processor error: {str(e)}")
        error_chunk = {"type": "error", "message": str(e)}
        yield f"data: {json.dumps(error_chunk)}\n\n"
