"""Basic tests for ORBIT Core components."""

import asyncio
import sys
import os

# Add orbit-core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from core.models import Source, SourceType, SourceStatus, URLCandidate, Opportunity, utc_now
from discovery.source_registry import SourceRegistry
from discovery.url_frontier import URLFrontier
from config.settings import settings
from crawler.http_crawler import SSRFProtection
from classifier.demand_detector import DemandDetector
from core.evidence import EvidenceTracker
from graph.knowledge_graph import KnowledgeGraph


def test_source_registry():
    """Test source registry functionality."""
    registry = SourceRegistry()
    
    # Register a source
    source = Source(
        source_type=SourceType.CANDIDATE_URL,
        domain="example.com",
        discovery_method="test",
    )
    source = registry.register_source(source)
    
    assert source.id is not None
    assert source.domain == "example.com"
    assert source.source_type == SourceType.CANDIDATE_URL
    
    # Test dedup - same domain should not be re-registered at same level
    source2 = Source(
        source_type=SourceType.CANDIDATE_URL,
        domain="example.com",
        discovery_method="test",
    )
    result = registry.register_source(source2)
    assert result.id == source.id  # Should return existing
    
    # Test promotion
    promoted = registry.promote_source(
        source.id,
        SourceType.VALIDATED_DOMAIN,
        SourceStatus.VALIDATED,
        validation_method="test",
        validation_score=0.9,
    )
    assert promoted.source_type == SourceType.VALIDATED_DOMAIN
    assert promoted.status == SourceStatus.VALIDATED
    
    # Test stats
    stats = registry.get_stats()
    assert stats["candidate_domains"] >= 1
    assert stats["validated_domains"] >= 1
    
    print("✓ Source registry tests passed")


def test_url_frontier():
    """Test URL frontier functionality."""
    from config.settings import ORBITSettings
    test_settings = ORBITSettings()
    test_settings.crawl_per_host_delay_seconds = 0
    frontier = URLFrontier(settings=test_settings)
    
    # Add URLs
    c1 = URLCandidate(url="https://example.com/page1", priority=3)
    c2 = URLCandidate(url="https://example.com/page2", priority=1)
    c3 = URLCandidate(url="https://example.com/page1", priority=5)  # Duplicate
    
    assert frontier.add(c1) is True
    assert frontier.add(c2) is True
    assert frontier.add(c3) is False  # Duplicate
    
    # Pop - highest priority first (priority=1 should come first)
    popped = frontier.pop()
    assert popped is not None
    assert popped.url == "https://example.com/page2"
    
    popped = frontier.pop()
    assert popped is not None
    assert popped.url == "https://example.com/page1"
    
    # Queue should be empty now
    popped = frontier.pop()
    assert popped is None
    
    stats = frontier.get_stats()
    assert stats["urls_added"] == 2
    assert stats["urls_popped"] == 2
    assert stats["duplicates_rejected"] == 1
    
    print("✓ URL frontier tests passed")


def test_ssrf_protection():
    """Test SSRF protection."""
    # Safe URLs
    assert SSRFProtection.is_safe("https://example.com") is True
    assert SSRFProtection.is_safe("http://example.com/path") is True
    
    # Unsafe URLs - private IPs
    assert SSRFProtection.is_safe("http://127.0.0.1") is False
    assert SSRFProtection.is_safe("http://10.0.0.1") is False
    assert SSRFProtection.is_safe("http://192.168.1.1") is False
    assert SSRFProtection.is_safe("http://172.16.0.1") is False
    
    # Unsafe URLs - blocked hosts
    assert SSRFProtection.is_safe("http://localhost") is False
    assert SSRFProtection.is_safe("http://169.254.169.254") is False
    
    # Unsafe schemes
    assert SSRFProtection.is_safe("ftp://example.com") is False
    assert SSRFProtection.is_safe("file:///etc/passwd") is False
    
    print("✓ SSRF protection tests passed")


def test_demand_detector():
    """Test demand detection."""
    detector = DemandDetector()
    
    # Positive case
    result = detector.detect(
        "Looking for a web developer to build an e-commerce website. Budget $5000.",
        source_url="https://example.com"
    )
    assert result.has_buying_intent is True
    assert result.buying_intent_score > 0
    assert result.confidence_score > 0
    
    # Negative case
    result = detector.detect(
        "This is a general discussion about web development best practices.",
        source_url="https://example.com"
    )
    assert result.has_buying_intent is False
    assert result.buying_intent_score == 0.0 or result.buying_intent_score < 0.3
    
    # Arabic
    result = detector.detect(
        "نبحث عن مصمم مواقع لإنشاء متجر إلكتروني",
        source_url="https://example.com"
    )
    assert result.has_buying_intent is True
    
    print("✓ Demand detector tests passed")


def test_knowledge_graph():
    """Test knowledge graph."""
    kg = KnowledgeGraph()
    
    # Add entities
    from core.models import Entity, Relationship
    from uuid import uuid4
    
    org = Entity(
        id=uuid4(),
        entity_type="organization",
        name="Acme Corp",
        attributes={"industry": "technology"},
    )
    person = Entity(
        id=uuid4(),
        entity_type="person",
        name="John Doe",
    )
    
    kg.add_entity(org)
    kg.add_entity(person)
    
    # Add relationship
    rel = Relationship(
        source_entity_id=org.id,
        target_entity_id=person.id,
        relationship_type="employs",
        confidence=1.0,
    )
    kg.add_relationship(rel)
    
    # Query
    found = kg.find_entities_by_name("Acme Corp")
    assert len(found) == 1
    assert found[0].name == "Acme Corp"
    
    rels = kg.get_relationships_for_entity(org.id)
    assert len(rels) == 1
    assert rels[0].relationship_type == "employs"
    
    stats = kg.get_stats()
    assert stats["entities"] == 2
    assert stats["relationships"] == 1
    
    print("✓ Knowledge graph tests passed")


def test_evidence_tracker():
    """Test evidence tracker."""
    tracker = EvidenceTracker()
    from uuid import uuid4
    
    source_id = uuid4()
    evidence = tracker.record_evidence(
        source_id=source_id,
        source_url="https://example.com",
        content="Looking for a web developer",
        confidence=0.9,
    )
    
    assert evidence.source_id == source_id
    assert evidence.content_hash is not None
    
    # Link to opportunity
    opp_id = uuid4()
    tracker.link_evidence_to_opportunity(opp_id, evidence.evidence_id)
    
    # Verify
    assert tracker.verify_opportunity_has_evidence(opp_id) is True
    
    # Get provenance
    tracker.add_provenance_step(
        opportunity_id=opp_id,
        step="detection",
        actor="demand_detector",
        confidence=0.9,
        evidence_ids=[evidence.evidence_id],
    )
    
    chain = tracker.get_provenance_chain(opp_id)
    assert len(chain) == 1
    assert chain[0].step == "detection"
    
    stats = tracker.get_stats()
    assert stats["evidence_records"] == 1
    
    print("✓ Evidence tracker tests passed")


if __name__ == "__main__":
    test_source_registry()
    test_url_frontier()
    test_ssrf_protection()
    test_demand_detector()
    test_knowledge_graph()
    test_evidence_tracker()
    print("\n✅ All core tests passed!")
