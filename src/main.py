#!/usr/bin/env python3
"""
AI Knowledge & Incident Management Platform
Main FastAPI application
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our modules
from .database import get_db, init_db
from .knowledge_service import KnowledgeService
from .incident_service import IncidentService
from .metrics import MetricsCollector
from .auth import verify_api_key, get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Knowledge & Incident Management Platform",
    description="Enterprise knowledge retrieval with AI-powered incident management",
    version="1.0.0",
    docs_url="/api/docs"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Demo only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize services
knowledge_service = KnowledgeService()
incident_service = IncidentService()
metrics = MetricsCollector()

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    include_incidents: bool = True

class SearchResult(BaseModel):
    title: str
    content: str
    relevance: float
    source: str
    document_type: str
    timestamp: Optional[datetime] = None

class IncidentClassifyRequest(BaseModel):
    description: str
    severity: str = "medium"
    priority: str = "normal"

class IncidentResponse(BaseModel):
    incident_id: str
    category: str
    suggested_procedures: List[str]
    estimated_resolution_time: str
    similar_incidents: List[Dict[str, Any]]
    auto_assigned_to: Optional[str] = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and load sample data"""
    logger.info("Starting AI Knowledge Platform...")
    
    # Initialize database
    await init_db()
    
    # Load sample data if not already loaded
    await knowledge_service.load_sample_data()
    await incident_service.load_sample_incidents()
    
    logger.info("✅ AI Knowledge Platform ready!")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    start_time = time.time()
    
    # Check database connectivity
    try:
        db_status = await knowledge_service.health_check()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = False
    
    # Check Ollama connectivity
    try:
        ollama_status = await knowledge_service.check_ollama()
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        ollama_status = False
    
    # Check ChromaDB connectivity
    try:
        chroma_status = await knowledge_service.check_chromadb()
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        chroma_status = False
    
    response_time = (time.time() - start_time) * 1000
    
    status = {
        "status": "healthy" if all([db_status, ollama_status, chroma_status]) else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": round(response_time, 2),
        "services": {
            "database": "up" if db_status else "down",
            "ollama": "up" if ollama_status else "down", 
            "chromadb": "up" if chroma_status else "down"
        },
        "version": "1.0.0"
    }
    
    metrics.record_health_check(response_time, status["status"] == "healthy")
    
    if status["status"] == "degraded":
        raise HTTPException(status_code=503, detail=status)
    
    return status

# Dashboard endpoint
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    stats = await get_dashboard_stats()
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "stats": stats}
    )

# Search endpoint
@app.post("/api/search")
async def search_knowledge(
    request: SearchRequest, 
    api_key: str = Depends(verify_api_key)
):
    """Search knowledge base with AI-powered semantic search"""
    start_time = time.time()
    
    try:
        # Perform semantic search
        results = await knowledge_service.search(
            query=request.query,
            max_results=request.max_results,
            include_incidents=request.include_incidents
        )
        
        search_time = (time.time() - start_time) * 1000
        
        # Calculate improvement metrics
        manual_search_time = 5 * 60 * 1000  # 5 minutes in ms
        improvement = ((manual_search_time - search_time) / manual_search_time) * 100
        
        metrics.record_search(search_time, len(results))
        
        return {
            "results": results,
            "query": request.query,
            "total_results": len(results),
            "search_time_ms": round(search_time, 2),
            "improvement_vs_manual": f"{improvement:.0f}% faster than manual search",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Incident classification endpoint
@app.post("/api/incidents/classify")
async def classify_incident(
    request: IncidentClassifyRequest,
    api_key: str = Depends(verify_api_key)
):
    """Classify incident and suggest resolution procedures"""
    start_time = time.time()
    
    try:
        # Classify incident using AI
        classification = await incident_service.classify_incident(
            description=request.description,
            severity=request.severity,
            priority=request.priority
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        metrics.record_incident_classification(processing_time, classification["category"])
        
        return {
            "incident_id": classification["incident_id"],
            "category": classification["category"],
            "confidence": classification["confidence"],
            "suggested_procedures": classification["procedures"],
            "estimated_resolution_time": classification["eta"],
            "similar_incidents": classification["similar"],
            "auto_assigned_to": classification.get("assigned_to"),
            "processing_time_ms": round(processing_time, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Incident classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

# Metrics endpoint
@app.get("/api/metrics")
async def get_metrics():
    """Get platform performance metrics"""
    return await metrics.get_metrics()

# Dashboard stats endpoint
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    stats = await metrics.get_dashboard_stats()
    
    # Add some demo business metrics
    stats.update({
        "business_impact": {
            "search_time_reduction": "67%",
            "mttr_improvement": "25%", 
            "knowledge_utilization": "+340%",
            "first_call_resolution": "+45%"
        },
        "cost_savings": {
            "monthly_savings": "$45,200",
            "productivity_gain": "34%",
            "support_tickets_reduced": "156"
        }
    })
    
    return stats

# Sample data endpoint for demo
@app.get("/api/demo/sample-search")
async def demo_search():
    """Demo search endpoint with pre-defined queries"""
    sample_queries = [
        "network troubleshooting procedures",
        "database connection timeout",
        "email server configuration",
        "security incident response",
        "backup and recovery procedures"
    ]
    
    results = []
    for query in sample_queries:
        search_results = await knowledge_service.search(query, max_results=3)
        results.append({
            "query": query,
            "results": search_results[:3],
            "result_count": len(search_results)
        })
    
    return {
        "demo_searches": results,
        "message": "These are sample searches showing the knowledge base capabilities"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint redirect to dashboard"""
    return JSONResponse({
        "message": "AI Knowledge & Incident Management Platform",
        "version": "1.0.0", 
        "endpoints": {
            "dashboard": "/dashboard",
            "api_docs": "/api/docs",
            "health": "/health",
            "search": "/api/search",
            "classify": "/api/incidents/classify"
        }
    })

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )