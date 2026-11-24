"""ORBIT Core data models.

Defines the fundamental data structures for the discovery network.
All models are Pydantic v2 for validation and serialization.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any, Set, Union
from pydantic import BaseModel, Field, HttpUrl
from uuid import uuid4, UUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# Source Classification (Requirement A: Distinguish clearly between types)
# =============================================================================

class SourceType(str, Enum):
    CANDIDATE_URL = "candidate_url"
    CANDIDATE_DOMAIN = "candidate_domain"
    VALIDATED_DOMAIN = "validated_domain"
    USEFUL_SOURCE = "useful_source"
    ACTIVE_MONITORED_SOURCE = "active_monitored_source"
    QUALIFIED_DEMAND_SOURCE = "qualified_demand_source"


class SourceStatus(str, Enum):
    DISCOVERED = "discovered"
    VALIDATING = "validating"
    VALIDATED = "validated"
    USEFUL = "useful"
    ACTIVE = "active"
    QUALIFIED = "qualified"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    EXPIRED = "expired"


# =============================================================================
# Core Entities
# =============================================================================

class Source(BaseModel):
    """A discovered source in the ORBIT network."""
    id: UUID = Field(default_factory=uuid4)
    source_type: SourceType
    status: SourceStatus = SourceStatus.DISCOVERED
    url: Optional[HttpUrl] = None
    domain: Optional[str] = None
    host: Optional[str] = None
    
    # Discovery metadata
    discovered_at: datetime = Field(default_factory=utc_now)
    discovered_from: Optional[UUID] = None  # Parent source that led to this
    discovery_generation: int = 0
    discovery_method: Optional[str] = None  # sitemap, rss, dns, ct, link, etc.
    
    # Validation metadata
    validated_at: Optional[datetime] = None
    validation_method: Optional[str] = None
    validation_score: Optional[float] = None
    
    # Quality metrics
    yield_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Activity tracking
    last_crawled: Optional[datetime] = None
    last_successful_crawl: Optional[datetime] = None
    crawl_count: int = 0
    failure_count: int = 0
    
    # Content metrics
    pages_discovered: int = 0
    pages_crawled: int = 0
    opportunities_found: int = 0
    
    # Geolocation & language
    country_code: Optional[str] = None
    region: Optional[str] = None
    language: Optional[str] = None
    language_confidence: Optional[float] = None
    
    # Relationships
    related_sources: Set[UUID] = Field(default_factory=set)
    parent_source: Optional[UUID] = None
    child_sources: Set[UUID] = Field(default_factory=set)
    
    # Provenance
    evidence_url: Optional[HttpUrl] = None
    evidence_snapshot: Optional[str] = None
    
    # Configuration
    is_excluded: bool = False
    exclusion_reason: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    
    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        use_enum_values = True


class URLCandidate(BaseModel):
    """A candidate URL discovered during crawling or source expansion."""
    id: UUID = Field(default_factory=uuid4)
    url: str
    source_id: Optional[UUID] = None
    domain: Optional[str] = None
    discovered_at: datetime = Field(default_factory=utc_now)
    discovery_method: Optional[str] = None
    
    # Filtering status
    is_filtered: bool = False
    filter_reason: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of: Optional[UUID] = None
    
    # Crawl status
    is_crawled: bool = False
    crawled_at: Optional[datetime] = None
    crawl_depth: int = 0
    
    # Prioritization
    priority: int = Field(default=5, ge=1, le=10)
    estimated_value: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Provenance
    evidence: Optional[str] = None


class Opportunity(BaseModel):
    """A qualified commercial opportunity discovered by ORBIT."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    
    # Source traceability (Requirement: every opportunity must have traceable evidence)
    source_id: UUID
    source_url: Optional[HttpUrl] = None
    evidence_snapshot: Optional[str] = None
    evidence_timestamp: Optional[datetime] = None
    
    # Classification
    service_category: Optional[str] = None
    industry: Optional[str] = None
    buying_intent_score: float = Field(default=0.0, ge=0.0, le=1.0)
    urgency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Requester information (only where publicly evidenced)
    requester_organization: Optional[str] = None
    requester_organization_confidence: Optional[float] = None
    requester_contact: Optional[str] = None
    requester_location: Optional[str] = None
    
    # Opportunity details
    budget_indicated: Optional[str] = None
    budget_confidence: Optional[float] = None
    deadline: Optional[datetime] = None
    requirements: List[str] = Field(default_factory=list)
    
    # Timestamps
    published_at: Optional[datetime] = None
    discovered_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    is_stale: bool = False
    is_fulfilled: bool = False
    
    # Competition
    visible_competitors: int = 0
    competition_score: float = Field(default=0.0, ge=0.0, le=1.0)
    competition_coverage_note: Optional[str] = None
    
    # Language & Geo
    language: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    
    # Deduplication
    is_duplicate: bool = False
    duplicate_of: Optional[UUID] = None
    cluster_id: Optional[str] = None
    
    # Status
    status: str = Field(default="new")  # new, qualified, contacted, closed, expired
    
    # Provenance
    provenance_chain: List[Dict[str, Any]] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Entity(BaseModel):
    """An entity in the knowledge graph (organization, person, product, etc.)."""
    id: UUID = Field(default_factory=uuid4)
    entity_type: str  # organization, person, product, service, community, website, opportunity
    name: str
    canonical_name: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    
    # Attributes
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Geolocation & language
    country_code: Optional[str] = None
    language: Optional[str] = None
    
    # Provenance
    source_ids: Set[UUID] = Field(default_factory=set)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Relationship(BaseModel):
    """A relationship between two entities in the knowledge graph."""
    id: UUID = Field(default_factory=uuid4)
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str  # e.g., "requests", "offers", "hosts", "mentions"
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    # Temporal
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    
    # Provenance
    source_ids: Set[UUID] = Field(default_factory=set)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    created_at: datetime = Field(default_factory=utc_now)


class CrawlJob(BaseModel):
    """A crawl job for distributed execution."""
    id: UUID = Field(default_factory=uuid4)
    url: str
    source_id: Optional[UUID] = None
    priority: int = Field(default=5)
    depth: int = 0
    scheduled_at: datetime = Field(default_factory=utc_now)
    
    # Execution
    worker_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = Field(default="pending")  # pending, running, completed, failed, dead_letter
    
    # Result
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    content_size: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 5
    
    # Content references
    raw_content_ref: Optional[str] = None  # Object storage reference
    extracted_content_ref: Optional[str] = None


class BenchmarkResult(BaseModel):
    """A benchmark measurement result."""
    id: UUID = Field(default_factory=uuid4)
    benchmark_name: str
    category: str  # discovery, crawling, extraction, classification, etc.
    metric_name: str
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=utc_now)
    
    # Classification of claim (Requirement J)
    claim_type: str  # Published Benchmark, Measured ORBIT Benchmark, Engineering Target, Conditional Scale Target, Unknown / Not Yet Measurable
    
    conditions: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


# =============================================================================
# Discovery Expansion Results
# =============================================================================

class DiscoveryResult(BaseModel):
    """Result of a discovery expansion cycle."""
    cycle_id: UUID = Field(default_factory=uuid4)
    seed_sources: int
    candidate_urls: int
    candidate_domains: int
    validated_domains: int
    useful_sources: int
    active_sources: int
    qualified_demand_sources: int
    new_opportunities: int
    duplicate_rate: float
    source_diversity_score: float
    expansion_rate: float
    marginal_yield: float
    timestamp: datetime = Field(default_factory=utc_now)


__all__ = [
    "SourceType", "SourceStatus", "Source", "URLCandidate", "Opportunity",
    "Entity", "Relationship", "CrawlJob", "BenchmarkResult", "DiscoveryResult",
    "utc_now",
]
