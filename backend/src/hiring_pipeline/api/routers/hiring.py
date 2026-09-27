from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from src.hiring_pipeline.logger_config import setup_logger
import warnings
from src.hiring_pipeline.pipelines.RAG_pipeline import RAGPipeline
from src.hiring_pipeline.api.dependencies import get_cassandra_session
from src.hiring_pipeline.components.CRUD_functions import *
from typing import Optional

log = setup_logger(__name__)
warnings.filterwarnings('ignore')

router = APIRouter(prefix="/hiring", tags=["Fetching Cassandra Hiring Data"])

class RequestQuery(BaseModel):
    query: str = Field(default="", description="query to search in the database")

class AddCandidateRequest(BaseModel):
    name: str = Field(..., description="Name of the candidate")
    email: str = Field(..., description="Email of the candidate")

class UpdateStageRequest(BaseModel):
    new_stage: Optional[str] = None

@router.post("/search")
def search_candidates(request: RequestQuery):
    if request.query.strip():
        log.info(f"Received search request with query: {request.query}")
        rag = RAGPipeline()
        rag.initialize_llm_model()
        return rag.generate_response(request.query)
    raise HTTPException(status_code=400, detail="Query parameter is empty. Please provide a valid query.")

@router.post("/candidates")
def add(request: AddCandidateRequest):
    session = get_cassandra_session()
    return add_candidate(name=request.name, email=request.email, session=session)

@router.get("/candidates")
def get_candidates():
    session = get_cassandra_session()
    return get_candidates_grouped(session=session)

@router.patch("/candidates/{candidate_id}/stage")
def move_candidate_stage(candidate_id: str, request: Optional[UpdateStageRequest] = None):
    session = get_cassandra_session()
    
    if request and request.new_stage == "Rejected":
        result = reject_candidate(candidate_id=candidate_id, session=session)
    else:
        result = move_stage(candidate_id=candidate_id, session=session)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/candidates/{candidate_id}/history")
def get_candidate_history(candidate_id: str):
    session = get_cassandra_session()
    history = get_history(candidate_id=candidate_id, session=session)
    if history is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return history

@router.get("/audit_logs")
def audit_logs(candidate_id: Optional[str] = None):
    session = get_cassandra_session()
    return get_audit_logs(session=session, candidate_id=candidate_id)
