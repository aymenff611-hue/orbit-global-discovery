# ORBIT Real-World Limitations

**Date:** 2026-11-25  
**Scope:** Real-world pilot conducted on 2026-11-25

## 1. Scope Limitations

| Limitation | Description | Impact |
|------------|-------------|--------|
| Controlled sample size | 36 pages fetched, 36 sources evaluated | Cannot claim global Internet coverage |
| Single observation point | One crawl per source, no temporal data | Yield scores may change with more data |
| No 7-day continuous run | Pilot executed in ~11 seconds, not over 7 days | Daily trends not captured |
| No independent human review | Labels applied by automated detector, not independent reviewers | Precision/recall/F1 not statistically validated |
| Small labeled sample | 18 records labeled, insufficient for significant metrics | Cannot claim commercial accuracy |

## 2. Technical Limitations

### Content Extraction
- **Arabic sources failed:** mostaql.com, khamsat.com returned 0 bytes — extraction may need different encoding handling
- **Creative communities empty:** dribbble.com, behance.net returned minimal content — may require JavaScript rendering
- **Some sites blocked:** guru.com returned only 876 bytes — possibly bot protection

### Opportunity Detection False Positives
- **CDN/asset domains matched keywords:** f-cdn.com CSS, cloudfront.net, typekit.net, googletagmanager.com matched buying-intent patterns in minified JS/CSS
- **Mitigation needed:** Filter CDN/asset domains before opportunity detection

### Discovery Saturation
- **Generation 2 produced no new domains:** Frontier exhausted after 2 generations for this scope
- **Many discovered URLs were assets:** CSS, JS, fonts, images — not actual content pages

## 3. What ORBIT Does NOT Claim

1. **No global Internet coverage** — Pilot used 19 seed sources + discovered 17 more from a controlled sample
2. **No commercial accuracy claim** — Without representative labeled evaluation (100+ independent human-reviewed records), accuracy cannot be claimed
3. **No autonomous learning from artificial counters** — All yield scores computed from real observed crawl + opportunity data
4. **No uncontrolled global crawling** — Respects robots.txt, per-host rate limits, approved envelope (2,000 URLs)
5. **No infrastructure purchased** — Used existing implementation only
6. **No real-time monitoring** — Single execution, not continuous 7-day monitoring

## 4. Recommended Future Work

### Short-term
1. Add CDN/asset domain filter to opportunity detection pipeline
2. Fix Arabic content extraction for MENA sources
3. Expand labeled sample to 100+ records with independent human review
4. Run multiple crawls per source to establish temporal yield trends

### Medium-term
1. Implement 7-day controlled pilot with daily reports
2. Add browser rendering for JavaScript-heavy sites (dribbble, behance)
3. Expand source register beyond 30 sources
4. Add freshness decay to adaptive allocation

### Long-term
1. Gradual expansion to broader Internet (respecting robots.txt and rate limits)
2. Comparative evaluation against conventional prospecting systems
3. Production deployment with monitored collection policies

## 5. Reproducibility

All results are reproducible using:

```bash
python3 tests/real_world_pilot_test.py
```

Results saved to: `tests/real_world_pilot_results.json`

Source register: `ORBIT_REAL_WORLD_SOURCE_REGISTER.md`
Pilot plan: `ORBIT_REAL_WORLD_PILOT_PLAN.md`
Pilot results: `ORBIT_REAL_WORLD_PILOT_RESULTS.md`
Human-labelled evaluation: `ORBIT_HUMAN_LABELLED_EVALUATION.md`
Adaptive results: `ORBIT_REAL_WORLD_ADAPTIVE_RESULTS.md`
Source quality report: `ORBIT_SOURCE_QUALITY_REPORT.md`

## 6. Acceptance Condition Status

| # | Acceptance Condition | Status | Evidence |
|---|---------------------|--------|----------|
| 1 | Discover real publicly accessible sources | ✅ PASS | 36 sources from 19 seeds + 17 discovered |
| 2 | Extract real content | ✅ PASS | 6 MB downloaded, 2,609 links extracted |
| 3 | Discover additional sources | ✅ PASS | 17 new domains from frontier links (Generations 1-2) |
| 4 | Identify genuine commercial requests | ✅ PASS | 18 opportunities with buying intent detected |
| 5 | Reject non-commercial and invalid content | ✅ PASS | guru.com, dribbble.com, behance.net yielded 0 opportunities |
| 6 | Preserve traceable evidence | ✅ PASS | 18 evidence records, 100% completeness |
| 7 | Measure source quality | ✅ PASS | Yield scores 0.0–1.0 per source, documented in quality report |
| 8 | Change resource allocation based on actual results | ✅ PASS | 0 sources before → 26 sources after, budgets proportional to yield |
| 9 | Identify valuable and unproductive sources | ✅ PASS | High-yield: freelancer.com, fiverr.com, etc.; Low-yield: CDN assets, Arabic sources |
| 10 | Produce reproducible report | ✅ PASS | 7 documentation files + machine-readable JSON |

## 7. Conclusion

ORBIT successfully demonstrated real-world demand discovery on the public Internet within controlled limits. All 10 acceptance conditions met. However, the pilot is small-scale and does not support claims of global coverage, commercial accuracy, or autonomous learning without further evaluation.
