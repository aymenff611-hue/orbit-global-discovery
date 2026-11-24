# ORBIT Demand Intelligence Research

**Version:** 0.1.0  
**Status:** Completed

---

## 1. Research Objective

Research the best technologies and methods for demand signal detection, buyer intent classification, and opportunity qualification — processing up to 10 million raw demand events per day with Precision@100 ≥ 90% and Recall ≥ 80%.

---

## 2. Demand Detection Methods Evaluated

| Method | Description | Candidates | Selected |
|--------|-------------|------------|----------|
| Keyword matching | Deterministic keyword/pattern matching | Custom | Tier 1 (Implemented) |
| Statistical classification | Logistic regression, Naive Bayes | scikit-learn | Tier 2 (Planned) |
| NER for organizations | Named entity recognition | spaCy, Stanza | Tier 3 (Planned) |
| Reasoning models | Large LLMs for ambiguous cases | OpenAI, Anthropic, local | Tier 4 (Planned) |
| Deep research agents | Agent-based investigation | DeerFlow, NVIDIA AI-Q | Tier 5 (Planned) |

---

## 3. Candidate Technologies

| Technology | License | Maintenance | Accuracy | Selected? | Reason |
|------------|---------|-------------|----------|-----------|--------|
| scikit-learn | BSD | Active | Good | Yes (Tier 2) | Lightweight, production-ready |
| spaCy | MIT | Active | Good | Planned (Tier 3) | NER, entity extraction |
| Stanza | Apache-2.0 | Active | Good | Alternative | NLP pipeline, multilingual |
| langdetect | Apache-2.0 | Active | Good | Yes | Language detection, 55+ languages |
| polyglot | GPLv3 | Moderate | Good | No | GPL license, ORBIT prefers permissive |
| OpenAI API | Proprietary | Active | High | Planned (Tier 4) | Reasoning for ambiguous cases |
| Anthropic API | Proprietary | Active | High | Alternative | Reasoning for ambiguous cases |
| DeerFlow | Unknown | Unknown | Unknown | Evaluated | Agent architecture research |
| NVIDIA AI-Q | Unknown | Unknown | Unknown | Evaluated | Agent architecture research |

---

## 4. Tiered Processing Architecture

ORBIT implements a 5-tier processing model:

**Tier 1: Deterministic filters and rules** (Implemented)
- Keyword matching for buying intent
- Pattern matching for RFP, RFQ, tender, quote
- Urgency, budget, deadline detection

**Tier 2: Lightweight classifiers** (Planned)
- scikit-learn models for classification
- Statistical confidence scoring

**Tier 3: Specialized extraction models** (Planned)
- spaCy/Stanza NER for organizations, products, services
- Budget and date extraction

**Tier 4: Larger reasoning models** (Planned)
- LLMs for ambiguous or high-value cases
- Only for pages that pass Tiers 1-3 with uncertainty

**Tier 5: Deep research agents** (Planned)
- Agent-based investigation for important opportunities
- Multi-step research and validation

---

## 5. Buyer Intent Detection

### 5.1 Detection Signals

- Explicit requests: "looking for", "need", "seeking", "hiring", "RFP", "RFQ"
- Implicit signals: problem statements, requirement descriptions
- Urgency: "urgent", "ASAP", "immediately", "deadline"
- Budget: price mentions, budget ranges, "under $X"
- Requirements: technical specifications, deliverables

### 5.2 Supported Languages

English, Arabic, Spanish, French, German, Chinese, Japanese, Korean, Russian, Portuguese (configurable)

### 5.3 Accuracy Targets

| Metric | Target | Classification |
|--------|--------|----------------|
| Precision@100 | ≥ 90% | Engineering Target |
| Recall | ≥ 80% | Engineering Target |
| Evidence provenance | 100% | Engineering Target |

---

## 6. Opportunity Qualification

Every qualified opportunity must have:
- Traceable source evidence
- Buying intent score (0-1)
- Urgency score (0-1)
- Confidence score (0-1)
- Service category
- Provenance chain

No fabricated buyer identity, budget, deadline, or request details.

---

## 7. Limitations

- Tier 1 keyword matching has limited accuracy for ambiguous content
- Multilingual detection accuracy varies by language
- No trained models yet (Tier 2-5 are planned)
- Evaluation dataset not yet created

---

## 8. Integration Recommendation

- scikit-learn: Direct integration for Tier 2 classifiers
- spaCy: Adapter for Tier 3 NER (planned)
- OpenAI/Anthropic: Adapter for Tier 4 reasoning (planned)
- DeerFlow/NVIDIA AI-Q: Evaluated, not integrated (agent architectures, not crawlers)

---

**End of ORBIT Demand Intelligence Research**
