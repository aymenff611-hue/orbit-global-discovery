"""ORBIT Control Plane API.

REST API for controlling and monitoring the ORBIT discovery network.
Endpoints for:
- Source management
- Discovery control
- Crawl job submission
- Opportunity retrieval
- System health and metrics
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from core.models import (
    Source, SourceType, SourceStatus, URLCandidate, Opportunity,
    CrawlJob, DiscoveryResult, BenchmarkResult,
)
from discovery.source_registry import SourceRegistry
from discovery.url_frontier import URLFrontier
from discovery.recursive_discovery import RecursiveDiscoveryEngine
from crawler.http_crawler import HTTPCrawler, SSRFProtection
from classifier.demand_detector import DemandDetector, DetectionResult

logger = logging.getLogger("orbit.api")

# Initialize core components
registry = SourceRegistry()
frontier = URLFrontier(settings=settings)
discovery_engine = RecursiveDiscoveryEngine(registry, frontier, settings=settings)
demand_detector = DemandDetector(settings=settings)

# Create FastAPI app
app = FastAPI(
    title="ORBIT Core API",
    description="Global Demand Discovery and Opportunity Intelligence Network",
    version="0.1.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request/Response Models
# =============================================================================

class SourceRegisterRequest(BaseModel):
    url: Optional[str] = None
    domain: Optional[str] = None
    source_type: SourceType = SourceType.CANDIDATE_URL
    discovery_method: Optional[str] = None
    priority: int = 5


class SourceResponse(BaseModel):
    id: UUID
    source_type: SourceType
    status: SourceStatus
    url: Optional[str] = None
    domain: Optional[str] = None
    yield_score: float
    quality_score: float
    opportunities_found: int
    created_at: datetime


class URLCandidateRequest(BaseModel):
    url: str
    source_id: Optional[UUID] = None
    discovery_method: Optional[str] = None
    priority: int = 5


class CrawlJobRequest(BaseModel):
    url: str
    source_id: Optional[UUID] = None
    priority: int = 5
    depth: int = 0


class DetectionRequest(BaseModel):
    text: str
    source_url: Optional[str] = None
    force_tier: Optional[int] = None


class OpportunityResponse(BaseModel):
    id: UUID
    title: str
    description: str
    source_id: UUID
    buying_intent_score: float
    urgency_score: float
    confidence_score: float
    status: str
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    components: Dict[str, str]


# =============================================================================
# Health and System Endpoints
# =============================================================================

@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """System health check."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now(),
        components={
            "registry": "ok",
            "frontier": "ok",
            "discovery_engine": "ok",
            "crawler": "ok",
            "detector": "ok",
        },
    )


@app.get("/api/v1/stats", tags=["System"])
async def get_stats():
    """Get system statistics."""
    return {
        "registry": registry.get_stats(),
        "frontier": frontier.get_stats(),
        "detector": demand_detector.get_stats(),
        "crawler": {},  # Will be populated when crawler runs
    }


# =============================================================================
# Source Management Endpoints
# =============================================================================

@app.post("/api/v1/sources", response_model=SourceResponse, tags=["Sources"])
async def register_source(request: SourceRegisterRequest):
    """Register a new source in the ORBIT registry."""
    source = Source(
        source_type=request.source_type,
        url=request.url,
        domain=request.domain,
        discovery_method=request.discovery_method,
        priority=request.priority,
    )
    source = registry.register_source(source)
    return SourceResponse(
        id=source.id,
        source_type=source.source_type,
        status=source.status,
        url=str(source.url) if source.url else None,
        domain=source.domain,
        yield_score=source.yield_score,
        quality_score=source.quality_score,
        opportunities_found=source.opportunities_found,
        created_at=source.created_at,
    )


@app.get("/api/v1/sources/{source_id}", response_model=SourceResponse, tags=["Sources"])
async def get_source(source_id: UUID):
    """Get a source by ID."""
    source = registry.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse(
        id=source.id,
        source_type=source.source_type,
        status=source.status,
        url=str(source.url) if source.url else None,
        domain=source.domain,
        yield_score=source.yield_score,
        quality_score=source.quality_score,
        opportunities_found=source.opportunities_found,
        created_at=source.created_at,
    )


@app.get("/api/v1/sources", tags=["Sources"])
async def list_sources(
    source_type: Optional[SourceType] = Query(None),
    status: Optional[SourceStatus] = Query(None),
    limit: int = Query(100, le=1000),
):
    """List sources with optional filtering."""
    if source_type:
        sources = registry.get_sources_by_type(source_type)
    elif status:
        sources = registry.get_sources_by_status(status)
    else:
        sources = list(registry._sources.values())[:limit]

    return [
        SourceResponse(
            id=s.id,
            source_type=s.source_type,
            status=s.status,
            url=str(s.url) if s.url else None,
            domain=s.domain,
            yield_score=s.yield_score,
            quality_score=s.quality_score,
            opportunities_found=s.opportunities_found,
            created_at=s.created_at,
        )
        for s in sources[:limit]
    ]


# =============================================================================
# URL Frontier Endpoints
# =============================================================================

@app.post("/api/v1/urls", tags=["URL Frontier"])
async def add_url_candidate(request: URLCandidateRequest):
    """Add a URL candidate to the frontier."""
    candidate = URLCandidate(
        url=request.url,
        source_id=request.source_id,
        discovery_method=request.discovery_method,
        priority=request.priority,
    )
    added = frontier.add(candidate)
    return {"added": added, "url": request.url}


@app.get("/api/v1/urls/next", tags=["URL Frontier"])
async def get_next_url():
    """Get the next URL to crawl from the frontier."""
    candidate = frontier.pop()
    if not candidate:
        return {"message": "No URLs available"}
    return {
        "id": str(candidate.id),
        "url": candidate.url,
        "priority": candidate.priority,
        "discovery_method": candidate.discovery_method,
    }


@app.get("/api/v1/frontier/stats", tags=["URL Frontier"])
async def frontier_stats():
    """Get URL frontier statistics."""
    return frontier.get_stats()


# =============================================================================
# Discovery Endpoints
# =============================================================================

@app.post("/api/v1/discovery/cycle", response_model=Dict[str, Any], tags=["Discovery"])
async def run_discovery_cycle(
    max_generations: int = Query(3, ge=1, le=10),
    max_new_urls: int = Query(10000, ge=1, le=100000),
):
    """Run a recursive discovery cycle."""
    # Get high-value seed sources
    seeds = discovery_engine.get_high_value_sources(min_yield=0.0, limit=50)
    if not seeds:
        # Use all candidate domains as seeds
        seeds = registry.get_sources_by_type(SourceType.CANDIDATE_DOMAIN)[:50]

    result = discovery_engine.run_cycle(
        seed_sources=seeds,
        max_generations=max_generations,
        max_new_urls=max_new_urls,
    )
    return {
        "cycle_id": str(result.cycle_id),
        "seed_sources": result.seed_sources,
        "candidate_urls": result.candidate_urls,
        "candidate_domains": result.candidate_domains,
        "validated_domains": result.validated_domains,
        "useful_sources": result.useful_sources,
        "active_sources": result.active_sources,
        "qualified_demand_sources": result.qualified_demand_sources,
        "new_opportunities": result.new_opportunities,
        "duplicate_rate": result.duplicate_rate,
        "source_diversity_score": result.source_diversity_score,
        "expansion_rate": result.expansion_rate,
        "marginal_yield": result.marginal_yield,
        "timestamp": result.timestamp.isoformat(),
    }


# =============================================================================
# Crawl Endpoints
# =============================================================================

@app.post("/api/v1/crawl", tags=["Crawl"])
async def submit_crawl_job(request: CrawlJobRequest):
    """Submit a URL for crawling."""
    # Safety check
    if not SSRFProtection.is_safe(request.url):
        raise HTTPException(status_code=400, detail="URL blocked by SSRF protection")

    # Add to frontier
    candidate = URLCandidate(
        url=request.url,
        source_id=request.source_id,
        priority=request.priority,
    )
    added = frontier.add(candidate)

    return {
        "submitted": added,
        "url": request.url,
        "message": "URL added to crawl frontier",
    }


@app.post("/api/v1/crawl/fetch", tags=["Crawl"])
async def fetch_url(url: str):
    """Fetch a single URL (for testing)."""
    async with HTTPCrawler(settings=settings) as crawler:
        result = await crawler.fetch(url)
    return result


# =============================================================================
# Demand Detection Endpoints
# =============================================================================

@app.post("/api/v1/detect", response_model=Dict[str, Any], tags=["Demand Detection"])
async def detect_demand(request: DetectionRequest):
    """Detect buying intent and demand signals in text."""
    result = demand_detector.detect(
        text=request.text,
        source_url=request.source_url,
        force_tier=request.force_tier,
    )
    return {
        "has_buying_intent": result.has_buying_intent,
        "buying_intent_score": result.buying_intent_score,
        "urgency_score": result.urgency_score,
        "confidence_score": result.confidence_score,
        "intent_type": result.intent_type,
        "organizations": result.organizations,
        "products_services": result.products_services,
        "budget_indicators": result.budget_indicators,
        "deadline_indicators": result.deadline_indicators,
        "evidence_snippets": result.evidence_snippets,
        "processing_tier": result.processing_tier,
        "source_url": result.source_url,
    }


# =============================================================================
# Opportunity Endpoints
# =============================================================================

@app.post("/api/v1/opportunities", response_model=OpportunityResponse, tags=["Opportunities"])
async def create_opportunity_from_detection(
    text: str,
    source_id: UUID,
    source_url: Optional[str] = None,
):
    """Create an opportunity from text detection."""
    source = registry.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    detection = demand_detector.detect(text=text, source_url=source_url)
    opportunity = demand_detector.to_opportunity(detection, source, text)

    return OpportunityResponse(
        id=opportunity.id,
        title=opportunity.title,
        description=opportunity.description,
        source_id=opportunity.source_id,
        buying_intent_score=opportunity.buying_intent_score,
        urgency_score=opportunity.urgency_score,
        confidence_score=opportunity.confidence_score,
        status=opportunity.status,
        created_at=opportunity.created_at,
    )


@app.get("/api/v1/opportunities", tags=["Opportunities"])
async def list_opportunities(
    limit: int = Query(100, le=1000),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
):
    """List detected opportunities."""
    # This is a stub - opportunities would come from a database in production
    return {
        "message": "Opportunity listing requires database backend",
        "count": 0,
        "opportunities": [],
    }


# =============================================================================
# Benchmark Endpoints
# =============================================================================

@app.get("/api/v1/benchmarks", tags=["Benchmarks"])
async def list_benchmarks():
    """List benchmark results."""
    return {
        "message": "Benchmark results stored in benchmark suite",
        "categories": [
            "source_discovery",
            "crawling",
            "extraction",
            "classification",
            "deduplication",
            "entity_resolution",
        ],
    }


@app.get("/", tags=["System"])
async def root():
    """API root."""
    return {
        "name": "ORBIT Core API",
        "version": "0.1.0",
        "description": "Global Demand Discovery and Opportunity Intelligence Network",
        "docs": "/api/v1/docs",
    }
