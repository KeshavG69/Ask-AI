import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator, cast
from uuid import UUID
from pydantic import BaseModel
from agno.agent import Agent
from agno.run.response import RunEvent, RunResponse
from agent import create_web_support_agent

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat_agents"])


# Request Schema
class ChatRequest(BaseModel):
    urls: List[str]
    query: str
    session_id: str
    company_name: str


async def stream_chat_response(
    query: str,
    agent: Agent,
) -> AsyncGenerator:
    """
    Stream agent response following Figma pattern.

    Args:
        query: User's question
        agent: Web support agent instance

    Yields:
        JSON chunks of agent response
    """
    try:
        logger.info(f"🚀 Starting agent stream for query: {query[:50]}...")

        # Run the agent with the query and stream the results
        response_stream = await agent.arun(
            query, stream=True, stream_intermediate_steps=True
        )

        # Stream all response chunks
        async for run_response_chunk in response_stream:
            run_response_chunk = cast(RunResponse, run_response_chunk)
            yield run_response_chunk.to_json()

        logger.info(f"✅ Agent stream completed successfully")

    except Exception as e:
        logger.error(f"❌ Error in agent stream: {str(e)}")
        error_response = RunResponse(
            content=str(e),
            event=RunEvent.run_error,
        )
        yield error_response.to_json()
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

        logger.info(f"🔍 Processing chat request for session: {request.session_id}")
        logger.info(f"📝 Query: {request.query[:100]}...")
        logger.info(
            f"🌐 URLs: {', '.join(request.urls[:3])}{'...' if len(request.urls) > 3 else ''}"
        )

        # Create new agent for each request
        logger.info(
            f"🆕 Creating new web support agent for session: {request.session_id}"
        )

        # Create new agent with provided URLs
        agent = create_web_support_agent(
            starting_urls=request.urls, company_name=request.company_name
        )

        logger.info(f"✅ Agent created successfully for {len(request.urls)} URLs")

        # Stream the response
        return StreamingResponse(
            stream_chat_response(
                request.query,
                agent,
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
