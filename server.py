from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title="AI Chat Widget API",
    description="Streaming AI chat API for website integration",
    version="1.0.0"
)

# Add CORS middleware for cross-origin requests (essential for widget embedding)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for widget embedding
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the chat router
app.include_router(router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Chat Widget API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
