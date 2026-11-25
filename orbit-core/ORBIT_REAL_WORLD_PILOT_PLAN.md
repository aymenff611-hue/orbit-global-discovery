# ORBIT Real-World Pilot Plan

**Date:** 2026-11-25  
**Purpose:** Validate ORBIT's real-world usefulness on the public Internet  
**Status:** Planned / Controlled scope

## 1. Scope and Limits

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Validated source candidates | 20–30 | Diverse but manageable |
| Initial candidate URLs | 500–2,000 | Experimental envelope |
| Discovery generations | 3+ | Where source relationships permit |
| Languages | Multiple | English, Arabic, French, German |
| Content mixture | Positive, negative, duplicate, expired, ambiguous | Realistic distribution |
| Pilot duration | Controlled (not 7 days of continuous crawling) | Respects environment limits |
| Collection policy | Public pages, permitted access, robots.txt respected | Ethical collection |

## 2. Source Categories

1. **Specialized service-request communities** — Guru, PeoplePerHour, Fiverr categories
2. **Public technical forums** — Reddit communities (r/forhire, r/slavelabour, r/jobbit)
3. **Independent professional communities** — Dribbble, Behance, Contra
4. **Niche directories** — We Work Remotely, Remote OK, Working Nomads
5. **Public project & procurement listings** — Freelancer.com project categories
6. **Industry-specific request platforms** — 99designs, Toptal, Upwork
7. **Regional and multilingual sources** — Mostaql, Khamsat, Bayt, Malt, Twago
8. **Smaller specialized platforms** — Wellfound, Malt.fr, Twago.com

## 3. Discovery Methodology

### Generation 0: Initial Seed Sources
- Fetch 19–30 seed source URLs
- Register each as a validated source
- Extract links from each page
- Detect opportunities from extracted content
- Record crawl results and evidence

### Generation 1: Discovered Sources
- Pop frontier with links from Generation 0
- Fetch up to 20 new candidate domains
- Register as candidate sources
- Detect opportunities, record evidence

### Generation 2: Further Expansion
- Pop frontier with links from Generation 1
- Fetch up to 15 new candidate domains
- Continue opportunity detection and evidence recording

## 4. Adaptive Resource Allocation

### Before Observations
- Run `AdaptiveDiscoveryEngine.allocate_resources()` on initial registry state
- Record allocation decisions (budget per source, priority scores)

### After Observations
- Force rebalance after all pages fetched and opportunities detected
- Re-run allocation with real observed yield scores
- Compare before/after allocations to demonstrate change based on actual performance

### Allocation Principles (observed, not artificial)
- High-yield sources receive greater priority (more budget)
- Low-yield sources explored less but not permanently discarded
- Uncertain sources receive controlled exploration bonus
- Stale sources receive lower priority (freshness decay)
- New source categories explored via exploration weight

## 5. Opportunity Evaluation Criteria

Each detected opportunity must include:
- Original URL
- Source identity (domain, source ID)
- Extracted supporting evidence (content snapshot + hash)
- Publication date or explicit "unknown" status
- Detection timestamp
- Confidence score (0–1)
- Reason for qualification
- Reason for rejection where applicable

## 6. Human-Labelled Evaluation

- Target: 100+ collected content records
- Labels: Genuine buying intent, Non-commercial discussion, Informational, Spam, Expired/fulfilled, Ambiguous, Duplicate
- Measure: Precision, Recall, F1, False-positive rate, Evidence completeness, Duplicate detection, Freshness accuracy
- Independent review for disputed cases

## 7. Source Intelligence Metrics

Per source: type, language, geography, accessibility, update frequency, new URLs discovered, unique pages fetched, qualified opportunities, opportunity yield, duplicate rate, freshness, visible competition, collection cost, reliability.

## 8. Machine-Readable Output

All results saved to `tests/real_world_pilot_results.json`:
- Pages fetched, failed, bytes downloaded
- Links extracted, unique sources discovered
- Opportunities detected, evidence records
- Discovery throughput, pages per second
- Evidence completeness, allocation changes
- Generation-by-generation metrics
- Newly discovered sources with provenance
- Rejected sources with reasons
- Adaptive allocations before/after

## 9. Reproducible Commands

```bash
# Run the real-world pilot
python3 tests/real_world_pilot_test.py

# Expected: all 9 hard assertions pass
# Results: tests/real_world_pilot_results.json
```

## 10. Limitations

- Pilot uses controlled sample (not global Internet coverage)
- No claim of commercial accuracy without representative labeled evaluation
- No claim of autonomous learning based on artificially modified counters
- No uncontrolled global crawling
- No infrastructure or services purchased
