"""ORBIT Demand Detection and Buyer Intent Classification.

Tiered processing architecture:
1. Deterministic filters and rules (keywords, patterns)
2. Lightweight classifiers (statistical/ML via scikit-learn)
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
        # Tier 2: Lightweight statistical classifier (lazy-loaded)
        self._tier2_model = None
        self._tier2_vectorizer = None
        # Tier 3: NER model (lazy-loaded)
        self._tier3_ner = None

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
            return self._ensure_python_types(tier1_result)

        # Tier 2: Lightweight classifier
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
            return self._ensure_python_types(tier3_result)

        # Return best result so far (tier 1 or 2)
        best = tier2_result or tier1_result
        best.processing_tier = best.processing_tier or 1
        if source_url:
            best.source_url = source_url
        return self._ensure_python_types(best)

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

        Uses scikit-learn when available. Falls back to rule-based enhancement
        when ML dependencies are not installed.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            import numpy as np

            # Lazy-load model if not cached
            if self._tier2_model is None:
                self._tier2_vectorizer = TfidfVectorizer(max_features=1000)
                self._tier2_model = LogisticRegression()
                # Train on synthetic labeled data (for demonstration)
                # In production, this would be trained on real labeled data
                train_texts = [
                    "looking for a web developer to build website",
                    "need a graphic designer for logo",
                    "hiring content writer for blog",
                    "request for proposal for software development",
                    "need translation services for documents",
                    "this is a general discussion about web development",
                    "hello how are you today",
                    "what is the best programming language",
                    "i like coffee in the morning",
                    "the weather is nice today",
                ]
                train_labels = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]  # 1=intent, 0=no intent

                X = self._tier2_vectorizer.fit_transform(train_texts)
                self._tier2_model.fit(X, train_labels)

            # Predict
            X = self._tier2_vectorizer.transform([text])
            prob = self._tier2_model.predict_proba(X)[0]
            intent_prob = prob[1] if len(prob) > 1 else prob[0]

            # Combine with tier 1
            combined_score = min(tier1.buying_intent_score + (intent_prob * 0.3), 1.0)
            combined_confidence = min(tier1.confidence_score + (intent_prob * 0.2), 1.0)

            result = DetectionResult(
                has_buying_intent=combined_score >= 0.4,
                buying_intent_score=combined_score,
                urgency_score=tier1.urgency_score,
                confidence_score=combined_confidence,
                organizations=tier1.organizations,
                products_services=tier1.products_services,
                budget_indicators=tier1.budget_indicators,
                deadline_indicators=tier1.deadline_indicators,
                intent_type=tier1.intent_type or ("explicit" if intent_prob >= 0.6 else "implicit"),
                evidence_snippets=tier1.evidence_snippets,
                processing_tier=2,
            )
            return self._ensure_python_types(result)

        except ImportError:
            # scikit-learn not available - return enhanced tier 1
            logger.debug("scikit-learn not available for Tier 2, using Tier 1 result")
            tier1.processing_tier = 2
            return self._ensure_python_types(tier1)
        except Exception as e:
            logger.debug(f"Tier 2 classification failed: {e}")
            tier1.processing_tier = 2
            return self._ensure_python_types(tier1)

    def _ensure_python_types(self, result: DetectionResult) -> DetectionResult:
        """Ensure all boolean/numeric fields are native Python types (not numpy)."""
        import numpy as np

        if isinstance(result.has_buying_intent, np.bool_):
            result.has_buying_intent = bool(result.has_buying_intent)
        if isinstance(result.buying_intent_score, (np.floating, np.integer)):
            result.buying_intent_score = float(result.buying_intent_score)
        if isinstance(result.urgency_score, (np.floating, np.integer)):
            result.urgency_score = float(result.urgency_score)
        if isinstance(result.confidence_score, (np.floating, np.integer)):
            result.confidence_score = float(result.confidence_score)
        return result

    def _tier3_extract(self, text: str, previous: DetectionResult) -> Optional[DetectionResult]:
        """Tier 3: Specialized extraction models.

        NER for organizations, products, services, budgets, dates.
        Uses simple pattern-based extraction as a lightweight NER substitute.
        """
        # Enhanced entity extraction beyond tier 1
        enhanced_orgs = list(previous.organizations)
        enhanced_products = list(previous.products_services)
        enhanced_budget = list(previous.budget_indicators)
        enhanced_deadline = list(previous.deadline_indicators)

        # Extract additional organizations (patterns like "at Company", "from Org")
        org_patterns = [
            r'(?i)at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
            r'(?i)from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
            r'(?i)company\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
            r'(?i)مؤسسة\s+([\u0621-\u064A\s]+)',
            r'(?i)شركة\s+([\u0621-\u064A\s]+)',
        ]
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            for m in matches[:3]:
                if m.strip() not in enhanced_orgs:
                    enhanced_orgs.append(m.strip())

        # Extract budget amounts more precisely
        budget_patterns = [
            r'(?i)\$\s*\d[\d,]*(\.\d+)?',
            r'(?i)\d+\s*(usd|eur|sar|aed|egp|gbp)',
            r'(?i)ميزانية\s*[:=]\s*([\d,]+)',
        ]
        for pattern in budget_patterns:
            matches = re.findall(pattern, text)
            for m in matches[:3]:
                if str(m) not in enhanced_budget:
                    enhanced_budget.append(str(m))

        # Compute tier 3 confidence based on entity richness
        entity_richness = min(
            (len(enhanced_orgs) * 0.1) +
            (len(enhanced_products) * 0.1) +
            (len(enhanced_budget) * 0.15) +
            (len(enhanced_deadline) * 0.15),
            0.4
        )

        tier3_confidence = min(previous.confidence_score + entity_richness, 0.95)

        return DetectionResult(
            has_buying_intent=previous.has_buying_intent,
            buying_intent_score=min(previous.buying_intent_score + entity_richness * 0.5, 1.0),
            urgency_score=previous.urgency_score,
            confidence_score=tier3_confidence,
            organizations=enhanced_orgs[:10],
            products_services=enhanced_products[:10],
            budget_indicators=enhanced_budget[:10],
            deadline_indicators=enhanced_deadline[:10],
            intent_type=previous.intent_type,
            evidence_snippets=previous.evidence_snippets,
            processing_tier=3,
        )

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


# Tier 4 and Tier 5 are placeholder architectures (require external LLM/agent integration)
# Tier 4: Larger reasoning model for ambiguous cases - requires LLM provider integration
# Tier 5: Deep research agent for important opportunities - requires agent framework integration
# These are documented as planned components, not implemented without external dependencies.
