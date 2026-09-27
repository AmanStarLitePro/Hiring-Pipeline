from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.hiring_pipeline.logger_config import setup_logger
import os
from dotenv import load_dotenv
from src.hiring_pipeline.api.routers import hiring

load_dotenv()

log = setup_logger(__name__)

app = FastAPI(title="Hiring Pipeline API",
              description="APIs for Hiring Pipeline",
              version="1.0.0"
              )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hiring.router)

@app.get("/")
def root():
    '''Basic health check endpoint.'''
    return {"status": "ok", "pipeline_loaded": hasattr(app.state, 'pipeline') and app.state.pipeline is not None}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 2))
    
    import sys
    is_production = "--prod" in sys.argv or os.getenv("ENVIRONMENT", "development") == "production"
    
    if is_production:
        uvicorn.run("src.hiring_pipeline.api.server:app", host="0.0.0.0", port=port, workers=workers)
    else:
        uvicorn.run("src.hiring_pipeline.api.server:app", host="0.0.0.0", port=port, reload=True)
