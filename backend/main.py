from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as player_router
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Fantasy Football AI Assistant",
    description="AI-powered fantasy football analysis using Claude",
    version="1.0.0"
)

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(player_router)

@app.get("/")
async def root():
    return {
        "message": "Fantasy Football AI API is running!",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)