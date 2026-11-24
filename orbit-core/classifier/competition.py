"""ORBIT Competition Intelligence.

Estimates visible competition using observable evidence only.
Never claims to know all competitors in the world.
Every competition score discloses observable coverage, evidence, and confidence.
"""

import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger("orbit.classifier.competition")


@dataclass
class CompetitionSignal:
    """A single observable competition signal."""
    signal_type: str  # provider_count, offer_count, engagement, saturation, etc.
    value: Any
    source: str  # Where the signal was observed
    confidence: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CompetitionScore:
    """Competition assessment for an opportunity."""
    opportunity_id: str
    visible_competitors: int
    competition_score: float  # 0-1, higher = more competition
    coverage_note: str  # Discloses what was observable
    confidence: float  # 0-1, confidence in the score
    signals: List[CompetitionSignal] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.now)


class CompetitionIntelligence:
    """Estimates visible competition from publicly observable evidence.

    Never claims to know all competitors. Every score discloses
    observable coverage, evidence, and confidence.
    """

    def __init__(self, settings=None):
        self.settings = settings
        self.observable_only = settings.competition_observable_only if settings else True
        self._stats = {
            "assessments_performed": 0,
            "signals_detected": 0,
        }

    def assess_competition(self, opportunity_id: str,
                           source_url: str,
                           page_content: str,
                           visible_responses: Optional[int] = None,
                           existing_offers: Optional[int] = None,
                           engagement_evidence: Optional[Dict[str, Any]] = None,
                           source_characteristics: Optional[Dict[str, Any]] = None) -> CompetitionScore:
        """Assess competition for an opportunity based on observable evidence.

        Args:
            opportunity_id: The opportunity being assessed
            source_url: URL where the opportunity was found
            page_content: Content of the source page
            visible_responses: Number of visible responses (if observable)
            existing_offers: Number of existing offers (if observable)
            engagement_evidence: Evidence of engagement/fulfillment
            source_characteristics: Source-specific characteristics

        Returns:
            CompetitionScore with observable evidence and confidence
        """
        signals: List[CompetitionSignal] = []

        # Signal 1: Visible responses/providers
        if visible_responses is not None:
            signals.append(CompetitionSignal(
                signal_type="visible_responses",
                value=visible_responses,
                source=source_url,
                confidence=0.9,  # Directly observable
            ))
        else:
            # Try to extract from content
            extracted = self._extract_response_count(page_content)
            if extracted is not None:
                signals.append(CompetitionSignal(
                    signal_type="visible_responses",
                    value=extracted,
                    source=source_url,
                    confidence=0.6,  # Extracted, less certain
                ))

        # Signal 2: Existing offers
        if existing_offers is not None:
            signals.append(CompetitionSignal(
                signal_type="existing_offers",
                value=existing_offers,
                source=source_url,
                confidence=0.9,
            ))
        else:
            extracted = self._extract_offer_count(page_content)
            if extracted is not None:
                signals.append(CompetitionSignal(
                    signal_type="existing_offers",
                    value=extracted,
                    source=source_url,
                    confidence=0.6,
                ))

        # Signal 3: Engagement evidence
        if engagement_evidence:
            signals.append(CompetitionSignal(
                signal_type="engagement",
                value=engagement_evidence,
                source=source_url,
                confidence=0.7,
            ))

        # Signal 4: Source characteristics
        if source_characteristics:
            signals.append(CompetitionSignal(
                signal_type="source_characteristics",
                value=source_characteristics,
                source=source_url,
                confidence=0.8,
            ))

        # Compute competition score
        visible_competitors = 0
        for sig in signals:
            if sig.signal_type == "visible_responses" and isinstance(sig.value, int):
                visible_competitors = max(visible_competitors, sig.value)
            elif sig.signal_type == "existing_offers" and isinstance(sig.value, int):
                visible_competitors = max(visible_competitors, sig.value)

        # Competition score: 0 = no visible competition, 1 = highly saturated
        competition_score = self._compute_score(signals, visible_competitors)

        # Coverage note - discloses what was observable
        coverage_note = self._generate_coverage_note(signals)

        # Confidence based on signal quality and count
        confidence = self._compute_confidence(signals)

        score = CompetitionScore(
            opportunity_id=opportunity_id,
            visible_competitors=visible_competitors,
            competition_score=competition_score,
            coverage_note=coverage_note,
            confidence=confidence,
            signals=signals,
        )

        self._stats["assessments_performed"] += 1
        self._stats["signals_detected"] += len(signals)

        logger.info(f"Competition assessed for {opportunity_id}: "
                    f"score={competition_score:.2f}, competitors={visible_competitors}, "
                    f"confidence={confidence:.2f}")

        return score

    def _extract_response_count(self, content: str) -> Optional[int]:
        """Try to extract response count from page content."""
        patterns = [
            r'(?i)(\d+)\s+(?:responses|replies|answers|bids|proposals)',
            r'(?i)(\d+)\s+(?:people|providers|vendors|freelancers)',
            r'(?i)(\d+)\s+(?:applicants|candidates)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return int(match.group(1))
        return None

    def _extract_offer_count(self, content: str) -> Optional[int]:
        """Try to extract offer count from page content."""
        patterns = [
            r'(?i)(\d+)\s+(?:offers|listings|gigs|services)',
            r'(?i)(\d+)\s+(?:available|open)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return int(match.group(1))
        return None

    def _compute_score(self, signals: List[CompetitionSignal],
                       visible_competitors: int) -> float:
        """Compute competition score from signals (0-1)."""
        score = 0.0

        # Base score from visible competitors (logarithmic scale)
        if visible_competitors > 0:
            import math
            score += min(math.log1p(visible_competitors) / math.log1p(100), 0.6)

        # Adjust based on signal confidence
        if signals:
            avg_confidence = sum(s.confidence for s in signals) / len(signals)
            score *= avg_confidence

        return min(score, 1.0)

    def _generate_coverage_note(self, signals: List[CompetitionSignal]) -> str:
        """Generate a note disclosing observable coverage."""
        if not signals:
            return "No observable competition signals. Score based on absence of evidence."

        signal_types = [s.signal_type for s in signals]
        parts = []

        if "visible_responses" in signal_types:
            parts.append("visible response counts")
        if "existing_offers" in signal_types:
            parts.append("existing offer counts")
        if "engagement" in signal_types:
            parts.append("engagement evidence")
        if "source_characteristics" in signal_types:
            parts.append("source characteristics")

        if not parts:
            return "Limited observable evidence."

        return "Observable: " + ", ".join(parts) + ". Coverage limited to this source only."

    def _compute_confidence(self, signals: List[CompetitionSignal]) -> float:
        """Compute confidence in the competition score."""
        if not signals:
            return 0.1

        # More signals = higher confidence
        signal_count_factor = min(len(signals) / 4.0, 1.0)

        # Average signal confidence
        avg_confidence = sum(s.confidence for s in signals) / len(signals)

        # Directly observable signals weigh more
        direct_signals = sum(1 for s in signals if s.confidence >= 0.8)
        direct_factor = min(direct_signals / max(len(signals), 1), 1.0)

        return min((signal_count_factor * 0.4) + (avg_confidence * 0.4) + (direct_factor * 0.2), 1.0)

    def get_stats(self) -> Dict[str, Any]:
        """Get competition intelligence statistics."""
        return dict(self._stats)


__all__ = ["CompetitionIntelligence", "CompetitionScore", "CompetitionSignal"]
