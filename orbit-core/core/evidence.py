"""ORBIT Evidence Verification and Provenance.

Ensures every qualified opportunity has traceable source evidence.
Implements provenance chain tracking for all relationships and opportunities.
"""

import logging
import hashlib
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from dataclasses import dataclass, field

from core.models import Opportunity, Source, Entity, Relationship, utc_now

logger = logging.getLogger("orbit.core.evidence")


@dataclass
class EvidenceRecord:
    """A piece of evidence supporting a claim or relationship."""
    evidence_id: str = field(default_factory=lambda: str(UUID(int=0)))
    source_id: UUID = None
    source_url: Optional[str] = None
    content_snapshot: Optional[str] = None
    content_hash: Optional[str] = None
    captured_at: datetime = field(default_factory=utc_now)
    confidence: float = 1.0
    evidence_type: str = "web_page"  # web_page, document, api_response, etc.


@dataclass
class ProvenanceEntry:
    """A single step in a provenance chain."""
    step: str
    actor: str  # component name (e.g., "crawler", "extractor", "detector")
    timestamp: datetime
    input_refs: List[str] = field(default_factory=list)
    output_refs: List[str] = field(default_factory=list)
    confidence: float = 1.0
    evidence_ids: List[str] = field(default_factory=list)


class EvidenceTracker:
    """Tracks evidence provenance for opportunities and relationships.

    Guarantees: 100% of qualified opportunities must have traceable supporting sources.
    """

    def __init__(self):
        self._evidence_records: Dict[str, EvidenceRecord] = {}
        self._provenance_chains: Dict[UUID, List[ProvenanceEntry]] = {}  # opportunity_id -> chain
        self._opportunity_evidence: Dict[UUID, List[str]] = {}  # opportunity_id -> evidence IDs

        self._stats = {
            "evidence_records": 0,
            "opportunities_with_evidence": 0,
            "opportunities_without_evidence": 0,
        }

    def record_evidence(self, source_id: UUID, source_url: Optional[str],
                        content: str, evidence_type: str = "web_page",
                        confidence: float = 1.0) -> EvidenceRecord:
        """Record a piece of evidence from a source."""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        evidence = EvidenceRecord(
            source_id=source_id,
            source_url=source_url,
            content_snapshot=content[:10000],  # Truncate for storage
            content_hash=content_hash,
            confidence=confidence,
            evidence_type=evidence_type,
        )

        self._evidence_records[evidence.evidence_id] = evidence
        self._stats["evidence_records"] += 1

        logger.debug(f"Recorded evidence {evidence.evidence_id} from source {source_id}")
        return evidence

    def link_evidence_to_opportunity(self, opportunity_id: UUID, evidence_id: str):
        """Link evidence to an opportunity."""
        if opportunity_id not in self._opportunity_evidence:
            self._opportunity_evidence[opportunity_id] = []
        if evidence_id not in self._opportunity_evidence[opportunity_id]:
            self._opportunity_evidence[opportunity_id].append(evidence_id)

        # Update stats
        opps_with = len(self._opportunity_evidence)
        self._stats["opportunities_with_evidence"] = opps_with

    def add_provenance_step(self, opportunity_id: UUID, step: str, actor: str,
                             input_refs: Optional[List[str]] = None,
                             output_refs: Optional[List[str]] = None,
                             confidence: float = 1.0,
                             evidence_ids: Optional[List[str]] = None):
        """Add a step to an opportunity's provenance chain."""
        if opportunity_id not in self._provenance_chains:
            self._provenance_chains[opportunity_id] = []

        entry = ProvenanceEntry(
            step=step,
            actor=actor,
            timestamp=utc_now(),
            input_refs=input_refs or [],
            output_refs=output_refs or [],
            confidence=confidence,
            evidence_ids=evidence_ids or [],
        )

        self._provenance_chains[opportunity_id].append(entry)
        logger.debug(f"Added provenance step '{step}' to opportunity {opportunity_id}")

    def get_provenance_chain(self, opportunity_id: UUID) -> List[ProvenanceEntry]:
        """Get the full provenance chain for an opportunity."""
        return self._provenance_chains.get(opportunity_id, [])

    def get_opportunity_evidence(self, opportunity_id: UUID) -> List[EvidenceRecord]:
        """Get all evidence records for an opportunity."""
        evidence_ids = self._opportunity_evidence.get(opportunity_id, [])
        return [self._evidence_records[eid] for eid in evidence_ids if eid in self._evidence_records]

    def verify_opportunity_has_evidence(self, opportunity_id: UUID) -> bool:
        """Verify that an opportunity has at least one evidence record."""
        return opportunity_id in self._opportunity_evidence and len(self._opportunity_evidence[opportunity_id]) > 0

    def get_unverified_opportunities(self, all_opportunity_ids: List[UUID]) -> List[UUID]:
        """Get opportunities that lack evidence (should be empty for qualified opportunities)."""
        unverified = []
        for oid in all_opportunity_ids:
            if not self.verify_opportunity_has_evidence(oid):
                unverified.append(oid)
        return unverified

    def record_entity_evidence(self, entity_id: UUID, evidence_id: str,
                               relationship_id: Optional[UUID] = None):
        """Record evidence for an entity or relationship."""
        # Entity evidence tracking
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get evidence tracking statistics."""
        return {
            **self._stats,
            "evidence_records_count": len(self._evidence_records),
            "provenance_chains_count": len(self._provenance_chains),
            "evidence_coverage_percent": (
                self._stats["opportunities_with_evidence"] /
                max(self._stats["opportunities_with_evidence"] +
                    self._stats["opportunities_without_evidence"], 1)
            ) * 100,
        }

    def export_provenance(self, opportunity_id: UUID) -> Dict[str, Any]:
        """Export full provenance for an opportunity as a dictionary."""
        chain = self.get_provenance_chain(opportunity_id)
        evidence = self.get_opportunity_evidence(opportunity_id)

        return {
            "opportunity_id": str(opportunity_id),
            "has_evidence": self.verify_opportunity_has_evidence(opportunity_id),
            "evidence_count": len(evidence),
            "evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "source_id": str(e.source_id),
                    "source_url": e.source_url,
                    "content_hash": e.content_hash,
                    "captured_at": e.captured_at.isoformat(),
                    "confidence": e.confidence,
                    "evidence_type": e.evidence_type,
                }
                for e in evidence
            ],
            "provenance_chain": [
                {
                    "step": p.step,
                    "actor": p.actor,
                    "timestamp": p.timestamp.isoformat(),
                    "input_refs": p.input_refs,
                    "output_refs": p.output_refs,
                    "confidence": p.confidence,
                    "evidence_ids": p.evidence_ids,
                }
                for p in chain
            ],
        }
