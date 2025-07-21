import logging
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator, cast
from uuid import UUID
from pydantic import BaseModel
from agno.agent import Agent
from agno.run.response import RunEvent, RunResponse
from agent import create_web_support_agent
from simple_processor import simple_process_stream

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat_agents"])


# Request Schema
class ChatRequest(BaseModel):
    urls: List[str]
    query: str
    session_id: str
    company_name: str
    api_key: str


async def stream_chat_response(
    query: str,
    agent: Agent,
) -> AsyncGenerator:
    """
    🚀 ULTRA-FAST STREAM RESPONSE WITH BACKEND PROCESSING
    
    Uses our streaming beast to process complex agno responses into clean chunks!

    Args:
        query: User's question
        agent: Web support agent instance

    Yields:
        Clean, processed chunks ready for direct frontend consumption
    """
    try:
        logger.info(f"🚀 Starting BEAST MODE stream for query: {query[:50]}...")

        # Run the agent with the query and stream the results
        raw_response_stream = await agent.arun(
            query, stream=True, stream_intermediate_steps=True
        )

        # 🍌 PROCESS THROUGH OUR SIMPLE BANANA PROCESSOR!
        async for processed_chunk in simple_process_stream(raw_response_stream):
            yield processed_chunk

        logger.info(f"✅ BEAST MODE stream completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error in BEAST MODE stream: {str(e)}")
        error_chunk = {
            "type": "error",
            "message": str(e)
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        return


@router.post("/chat")
async def chat_agent(request: ChatRequest):
    """
    Chat Agent endpoint with streaming response for web content questions.

    Args:
        request: ChatRequest parameters including urls, query, and session_id

    Returns:
        StreamingResponse of the agent's response
    """
    try:
        # Basic validation
        if not request.session_id:
            raise HTTPException(
                status_code=400, detail="Session ID is required and cannot be empty"
            )
        if not request.query or request.query.strip() == "":
            raise HTTPException(
                status_code=400, detail="Query is required and cannot be empty"
            )
        if not request.urls or len(request.urls) == 0:
            raise HTTPException(status_code=400, detail="At least one URL is required")
        if not request.api_key or not request.api_key.strip():
            raise HTTPException(status_code=400, detail="API key is required")
        if not request.api_key.startswith('sk-'):
            raise HTTPException(status_code=400, detail="Invalid API key format. OpenAI API keys start with 'sk-'")

        logger.info(f"🔍 Processing chat request for session: {request.session_id}")
        logger.info(f"📝 Query: {request.query[:100]}...")
        logger.info(
            f"🌐 URLs: {', '.join(request.urls[:3])}{'...' if len(request.urls) > 3 else ''}"
        )

        # Create new agent for each request
        logger.info(
            f"🆕 Creating new web support agent for session: {request.session_id}"
        )

        # Create new agent with provided URLs and API key
        agent = create_web_support_agent(
            starting_urls=request.urls, 
            company_name=request.company_name,
            api_key=request.api_key,
            session_id=request.session_id
        )

        logger.info(f"✅ Agent created successfully for {len(request.urls)} URLs")

        # Stream the response
        return StreamingResponse(
            stream_chat_response(
                request.query,
                agent
            ),
            media_type="text/event-stream",
        )

    except Exception as e:
        logger.error(f"❌ Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Chat Widget API"}
