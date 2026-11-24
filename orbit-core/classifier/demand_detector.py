"""ORBIT Demand Detection and Buyer Intent Classification.

Tiered processing architecture:
1. Deterministic filters and rules (keywords, patterns)
2. Lightweight classifiers (statistical/ML)
3. Specialized extraction models (NER for organizations, budgets, dates)
4. Larger reasoning models for ambiguous cases
5. Deep research agents for important opportunities

Every detected opportunity must have traceable source evidence.
"""

import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field

from core.models import Opportunity, Source, utc_now

logger = logging.getLogger("orbit.classifier.demand_detector")


@dataclass
class DetectionResult:
    """Result of demand detection on a piece of content."""
    has_buying_intent: bool
    buying_intent_score: float  # 0-1
    urgency_score: float  # 0-1
    confidence_score: float  # 0-1
    
    # Detected entities
    organizations: List[str] = field(default_factory=list)
    products_services: List[str] = field(default_factory=list)
    budget_indicators: List[str] = field(default_factory=list)
    deadline_indicators: List[str] = field(default_factory=list)
    location_indicators: List[str] = field(default_factory=list)
    
    # Classification
    service_category: Optional[str] = None
    intent_type: Optional[str] = None  # explicit, implicit, none
    
    # Evidence
    evidence_snippets: List[str] = field(default_factory=list)
    source_url: Optional[str] = None
    
    # Processing tier used
    processing_tier: int = 1
    
    # Timestamps
    detected_at: datetime = field(default_factory=utc_now)


class DemandDetector:
    """Detects buying intent and demand signals in content.

    Uses a tiered approach to avoid sending every page to expensive models.
    """

    # Tier 1: Deterministic keywords and patterns
    BUYING_INTENT_KEYWORDS = [
        # English
        "looking for", "need a", "need an", "require", "seeking", "searching for",
        "hiring", "freelancer", "contractor", "consultant", "agency", "company",
        "provider", "vendor", "supplier", "quote", "proposal", "bid", "tender",
        "rfp", "request for proposal", "request for quote", "project",
        "budget", "price", "cost", "rate", "hourly", "fixed price",
        "can you", "do you", "are you available", "interested in",
        # Arabic
        "بحوث عن", "بحت عن", "need", "نبحث عن", "نحتاج إلى", "نحتاج",
        "مستقل", "مستقلين", "مكتب", "شركة", "مؤسسة", "عرض سعر", "عرض",
        "مناقصة", "مناقصة", "مشروع", "ميزانية", "سعر", "تكلفة",
        "متوفر", "متاحة", "مهتم", "مهتمين",
    ]

    EXPLICIT_INTENT_PATTERNS = [
        r"(?i)(looking for|seeking|need|require|hiring|searching for)\s+(.{0,100})",
        r"(?i)(request for|rfp|rfq|proposal|quote|bid|tender)\s+(.{0,100})",
        r"(?i)(نبحث عن|نحتاج|بحت عن|يبحثون عن)\s+(.{0,100})",
        r"(?i)(عرض سعر|مناقصة|مشروع|ميزانية)\s+(.{0,100})",
    ]

    URGENCY_PATTERNS = [
        r"(?i)(urgent|as soon as possible|asap|immediately|right now|quickly|fast)",
        r"(?i)(عاجل|فوري|سريع|فوراً|أسرع ما يمكن)",
    ]

    BUDGET_PATTERNS = [
        r"(?i)(budget|\$\d+|\d+\s*(usd|eur|sar|aed|egp)|price|cost|rate)",
        r"(?i)(ميزانية|سعر|تكلفة| ريال|درهم|دولار|جنيه)",
    ]

    DEADLINE_PATTERNS = [
        r"(?i)(deadline|by\s+\w+\s+\d+|due\s+on|until\s+\w+|before\s+\w+)",
        r"(?i)(موعد نهائي|تاريخ|حتى|قبل)",
    ]

    def __init__(self, settings=None):
        self.settings = settings
        self._stats = {
            "contents_analyzed": 0,
            "intent_detected": 0,
            "by_tier": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "false_positives": 0,
        }
        self._compiled_patterns = [
            re.compile(p) for p in self.EXPLICIT_INTENT_PATTERNS
        ]

    def detect(self, text: str, source_url: Optional[str] = None,
               source: Optional[Source] = None,
               force_tier: Optional[int] = None) -> DetectionResult:
        """Detect buying intent and demand signals in text.

        Tiered processing:
        - Tier 1: Deterministic keyword/pattern matching (always runs)
        - Tier 2: Lightweight statistical classifier (if Tier 1 is ambiguous)
        - Tier 3: Specialized extraction models (NER for orgs, budgets, dates)
        - Tier 4: Larger reasoning model (for ambiguous high-value cases)
        - Tier 5: Deep research agent (for important opportunities)
        """
        self._stats["contents_analyzed"] += 1

        # Tier 1: Deterministic detection
        tier1_result = self._tier1_detect(text)
        self._stats["by_tier"][1] += 1

        if tier1_result.has_buying_intent and tier1_result.confidence_score >= 0.8:
            # High confidence from tier 1, no need for deeper processing
            tier1_result.processing_tier = 1
            if source_url:
                tier1_result.source_url = source_url
            self._stats["intent_detected"] += 1
            return tier1_result

        # Tier 2: Lightweight classifier (if available)
        tier2_result = self._tier2_classify(text, tier1_result)
        if tier2_result and tier2_result.confidence_score >= 0.7:
            tier2_result.processing_tier = 2
            if source_url:
                tier2_result.source_url = source_url
            self._stats["intent_detected"] += 1
            return tier2_result

        # Tier 3: Specialized extraction (NER, etc.)
        tier3_result = self._tier3_extract(text, tier2_result or tier1_result)
        if tier3_result and tier3_result.confidence_score >= 0.6:
            tier3_result.processing_tier = 3
            if source_url:
                tier3_result.source_url = source_url
            self._stats["intent_detected"] += 1
            return tier3_result

        # Return best result so far (tier 1 or 2)
        best = tier2_result or tier1_result
        best.processing_tier = best.processing_tier or 1
        if source_url:
            best.source_url = source_url
        return best

    def _tier1_detect(self, text: str) -> DetectionResult:
        """Tier 1: Deterministic keyword and pattern matching."""
        text_lower = text.lower()

        # Count keyword matches
        keyword_matches = []
        for kw in self.BUYING_INTENT_KEYWORDS:
            if kw.lower() in text_lower:
                keyword_matches.append(kw)

        # Match explicit patterns
        pattern_matches = []
        for pattern in self._compiled_patterns:
            match = pattern.search(text)
            if match:
                pattern_matches.append(match.group(0)[:100])

        # Check urgency
        urgency_matches = [p for p in self.URGENCY_PATTERNS if re.search(p, text)]
        urgency_score = min(len(urgency_matches) * 0.3, 1.0)

        # Check budget
        budget_matches = [p for p in self.BUDGET_PATTERNS if re.search(p, text)]
        has_budget = len(budget_matches) > 0

        # Check deadline
        deadline_matches = [p for p in self.DEADLINE_PATTERNS if re.search(p, text)]
        has_deadline = len(deadline_matches) > 0

        # Compute buying intent score
        intent_score = 0.0
        if keyword_matches:
            intent_score += min(len(keyword_matches) * 0.15, 0.6)
        if pattern_matches:
            intent_score += min(len(pattern_matches) * 0.2, 0.4)
        if has_budget:
            intent_score += 0.2
        if has_deadline:
            intent_score += 0.1
        intent_score = min(intent_score, 1.0)

        has_intent = intent_score >= 0.3 or len(pattern_matches) > 0

        # Confidence based on pattern matches and keyword density
        confidence = min(
            (len(pattern_matches) * 0.3) + (len(keyword_matches) * 0.05) + (0.2 if has_budget else 0),
            1.0
        )

        # Extract entities (simple)
        organizations = self._extract_simple_organizations(text)
        products = self._extract_products_services(text)

        return DetectionResult(
            has_buying_intent=has_intent,
            buying_intent_score=intent_score,
            urgency_score=urgency_score,
            confidence_score=confidence,
            organizations=organizations,
            products_services=products,
            budget_indicators=budget_matches,
            deadline_indicators=deadline_matches,
            intent_type="explicit" if pattern_matches else ("implicit" if keyword_matches else "none"),
            evidence_snippets=pattern_matches[:5],
            processing_tier=1,
        )

    def _tier2_classify(self, text: str, tier1: DetectionResult) -> Optional[DetectionResult]:
        """Tier 2: Lightweight statistical classifier.

        This is a placeholder for a lightweight ML classifier (e.g., logistic
        regression, Naive Bayes, or small transformer). In production, this
        would be a trained model on labeled demand data.
        """
        # Placeholder: return None to indicate tier 2 not implemented yet
        # A real implementation would load a trained model here
        return None

    def _tier3_extract(self, text: str, previous: DetectionResult) -> Optional[DetectionResult]:
        """Tier 3: Specialized extraction models.

        NER for organizations, products, services, budgets, dates.
        Placeholder for spaCy, Stanza, or similar NER models.
        """
        # Placeholder: return None to indicate tier 3 not implemented yet
        return None

    def _extract_simple_organizations(self, text: str) -> List[str]:
        """Simple organization extraction using capitalized word patterns."""
        orgs = []
        # Match patterns like "Company Name", "Organization X"
        pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b')
        matches = pattern.findall(text)
        orgs.extend(matches[:5])
        return orgs

    def _extract_products_services(self, text: str) -> List[str]:
        """Simple product/service extraction."""
        products = []
        # Look for common service indicators
        service_words = ["design", "development", "marketing", "consulting",
                        "writing", "translation", "programming", "development",
                        "تصميم", "تطوير", "تسويق", "استشارات", "كتابة", "ترجمة", "برمجة"]
        text_lower = text.lower()
        for word in service_words:
            if word in text_lower:
                products.append(word)
        return list(set(products))[:5]

    def to_opportunity(self, detection: DetectionResult, source: Source,
                       content_text: str) -> Opportunity:
        """Convert a detection result to an Opportunity record."""
        return Opportunity(
            title=self._generate_title(detection, source),
            description=content_text[:2000],  # Truncate for storage
            source_id=source.id,
            source_url=str(source.url) if source.url else None,
            evidence_snapshot=content_text[:500],  # Store evidence snippet
            evidence_timestamp=utc_now(),
            service_category=detection.service_category,
            buying_intent_score=detection.buying_intent_score,
            urgency_score=detection.urgency_score,
            confidence_score=detection.confidence_score,
            requester_organization=detection.organizations[0] if detection.organizations else None,
            requirements=detection.products_services,
            language=getattr(source, 'language', None),
            country_code=getattr(source, 'country_code', None),
            provenance_chain=[
                {
                    "step": "detection",
                    "tier": detection.processing_tier,
                    "source_id": str(source.id),
                    "timestamp": detection.detected_at.isoformat(),
                    "confidence": detection.confidence_score,
                }
            ],
            status="new",
        )

    def _generate_title(self, detection: DetectionResult, source: Source) -> str:
        """Generate a title for the opportunity."""
        if detection.products_services:
            return f"Demand for {detection.products_services[0]}"
        if detection.organizations:
            return f"Service request from {detection.organizations[0]}"
        return f"Opportunity from {source.domain or source.url}"

    def get_stats(self) -> dict:
        return dict(self._stats)
