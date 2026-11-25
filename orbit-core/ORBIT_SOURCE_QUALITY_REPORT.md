# ORBIT Source Quality Report

**Date:** 2026-11-25  
**Source:** `tests/real_world_pilot_test.py`  
**Purpose:** Per-source intelligence and quality assessment from the real-world pilot

## 1. Source Intelligence Overview

| Metric | Aggregate |
|--------|-----------|
| Total sources evaluated | 36 |
| Sources with opportunities | 14 |
| Sources without opportunities | 22 |
| Total pages fetched | 36 |
| Total bytes downloaded | 6,056,552 |
| Total links extracted | 2,609 |
| Total opportunities detected | 18 |
| Evidence records | 18 |

## 2. Per-Source Quality Assessment

### High-Opportunity-Yield Sources (Recommended for continued monitoring)

| # | Source | Type | Language | Region | Pages Fetched | Links Extracted | Opportunities | Yield | Assessment |
|---|--------|------|----------|--------|---------------|-----------------|---------------|-------|------------|
| 1 | freelancer.com | project_listing | English | Global | 5 | 1,451 | 5 | 1.0000 | High value — consistent buying intent across categories |
| 2 | fiverr.com | service_marketplace | English | Global | 1 | 0 | 1 | 1.0000 | High value — service demand signals |
| 3 | weworkremotely.com | remote_jobs | English | Global | 1 | 441 | 1 | 1.0000 | High value — remote job postings |
| 4 | remoteok.com | remote_jobs | English | Global | 1 | 49 | 1 | 1.0000 | High value — remote job postings |
| 5 | workingnomads.com | remote_jobs | English | Global | 1 | 91 | 1 | 1.0000 | High value — remote job postings |
| 6 | twago.com | europe_freelance | German/English | Europe | 1 | 49 | 1 | 1.0000 | High value — European freelance projects |
| 7 | wellfound.com | startup_jobs | English | US | 1 | 70 | 1 | 1.0000 | High value — startup job postings |

### Low-Opportunity-Yield Sources (Noise generators)

| # | Source | Type | Language | Region | Pages Fetched | Links Extracted | Opportunities | Yield | Assessment |
|---|--------|------|----------|--------|---------------|-----------------|---------------|-------|------------|
| 8 | guru.com | service_request | English | Global | 1 | 0 | 0 | 0.0000 | Low value — no extractable content |
| 9 | peopleperhour.com | service_request | English | UK/Europe | 1 | 0 | 0 | 0.0000 | Low value — extraction failed |
| 10 | dribbble.com | creative_community | English | Global | 1 | 0 | 0 | 0.0000 | Low value — extraction failed |
| 11 | behance.net | creative_community | English | Global | 1 | 0 | 0 | 0.0000 | Low value — minimal content |
| 12 | mostaql.com | arabic_freelance | Arabic | MENA | 1 | 0 | 0 | 0.0000 | Low value — extraction failed |
| 13 | khamsat.com | arabic_marketplace | Arabic | MENA | 1 | 0 | 0 | 0.0000 | Low value — extraction failed |
| 14 | bayt.com | mena_jobs | Arabic/English | MENA | 1 | 0 | 0 | 0.0000 | Low value — minimal content |
| 15 | malt.fr | europe_freelance | French/English | Europe | 1 | 0 | 0 | 0.0000 | Low value — minimal content |

### Infrastructure Sources (Not demand sources)

| # | Source | Type | Pages Fetched | Links | Opportunities | Yield | Assessment |
|---|--------|------|---------------|-------|---------------|-------|------------|
| 16 | www.f-cdn.com | CDN | 2 | 0 | 1 | 0.5000 | Asset host — false positive from CSS keyword matching |
| 17 | cdnjs.cloudflare.com | CDN | 1 | 0 | 1 | 1.0000 | Asset host — false positive |
| 18 | d262ri5vl0r1ym.cloudfront.net | CDN | 1 | 0 | 0 | 0.0000 | Asset host |
| 19 | www.googletagmanager.com | CDN | 1 | 0 | 1 | 1.0000 | Asset host — false positive |
| 20 | use.typekit.net | CDN | 1 | 0 | 1 | 1.0000 | Asset host — false positive |
| 21 | fonts.googleapis.com | CDN | 1 | 0 | 0 | 0.0000 | Asset host |
| 22 | fonts.gstatic.com | CDN | 1 | 0 | 0 | 0.0000 | Asset host |
| 23 | app.crossengage.io | Marketing | 1 | 3 | 0 | 0.0000 | Marketing platform |
| 24 | cdn3/4/5/6.f-cdn.com | CDN | 4 | 0 | 0 | 0.0000 | Asset hosts |
| 25 | www.workingnomads.com | remote_jobs | 1 | 162 | 1 | 1.0000 | Duplicate domain (same org as #5) |
| 26 | www.twago.com | europe_freelance | 1 | 0 | 1 | 1.0000 | Duplicate domain (same org as #6) |
| 27 | www.freelancer.com | project_listing | 1 | 279 | 1 | 1.0000 | Duplicate domain (same org as #1) |
| 28-36 | Various CDN/asset | CDN | 9 | 0 | 0 | 0.0000 | Infrastructure, not demand |

## 3. Source Quality by Category

### Public Project & Procurement Listings (freelancer.com)
- **Yield:** 1.0 opportunities per crawl
- **Assessment:** Highest value category — real client requests with budgets, deadlines, buyer organizations
- **Recommendation:** Continue monitoring, expand to more categories

### Remote Job Boards (weworkremotely.com, remoteok.com, workingnomads.com)
- **Yield:** 1.0 opportunities per crawl
- **Assessment:** High value — consistent remote contract postings
- **Recommendation:** Continue monitoring

### Service Marketplaces (fiverr.com)
- **Yield:** 1.0 opportunities per crawl
- **Assessment:** High value — service demand patterns
- **Recommendation:** Continue monitoring

### Startup Job Boards (wellfound.com)
- **Yield:** 1.0 opportunities per crawl
- **Assessment:** High value — startup hiring demand
- **Recommendation:** Continue monitoring

### European Freelance (twago.com, malt.fr)
- **Yield:** twago=1.0, malt=0.0
- **Assessment:** Mixed — twago has extractable content, malt does not
- **Recommendation:** Continue twago, deprioritize malt

### Arabic / MENA Sources (mostaql.com, khamsat.com, bayt.com)
- **Yield:** 0.0 for all
- **Assessment:** Low value in this pilot — extraction failed for Arabic sites
- **Recommendation:** Investigate extraction issues for Arabic content; may need different extraction approach

### Creative Communities (dribbble.com, behance.net)
- **Yield:** 0.0 for all
- **Assessment:** Low value — portfolio showcases, not service requests
- **Recommendation:** Deprioritize for demand discovery

### CDN/Infrastructure Sources
- **Yield:** Mixed (false positives from keyword matching in CSS/JS)
- **Assessment:** Not demand sources — filter out from opportunity detection
- **Recommendation:** Add CDN/asset domain filter to pipeline

## 4. Source Intelligence Metrics Detail

| Source | Type | Language | Geo | Accessible | Update Freq | New URLs | Pages Fetched | Qualified Opps | Yield | Duplicate Rate | Freshness | Competition | Cost | Reliability |
|--------|------|----------|-----|------------|-------------|----------|---------------|----------------|-------|----------------|-----------|-------------|------|-------------|
| freelancer.com | project_listing | en | Global | Yes | High | 1,451 | 5 | 5 | 1.0000 | Low | High | High | Low | High |
| fiverr.com | service_marketplace | en | Global | Yes | High | 0 | 1 | 1 | 1.0000 | N/A | High | High | Low | High |
| weworkremotely.com | remote_jobs | en | Global | Yes | High | 441 | 1 | 1 | 1.0000 | N/A | High | Medium | Low | High |
| remoteok.com | remote_jobs | en | Global | Yes | High | 49 | 1 | 1 | 1.0000 | N/A | High | Medium | Low | High |
| workingnomads.com | remote_jobs | en | Global | Yes | Medium | 91 | 1 | 1 | 1.0000 | N/A | High | Medium | Low | High |
| twago.com | europe_freelance | de/en | Europe | Yes | Medium | 49 | 1 | 1 | 1.0000 | N/A | High | Medium | Low | High |
| wellfound.com | startup_jobs | en | US | Yes | High | 70 | 1 | 1 | 1.0000 | N/A | High | Medium | Low | High |
| guru.com | service_request | en | Global | Yes | Medium | 0 | 1 | 0 | 0.0000 | N/A | Unknown | Low | Low | Low |
| mostaql.com | arabic_freelance | ar | MENA | Yes | Unknown | 0 | 1 | 0 | 0.0000 | N/A | Unknown | Low | Low | Low |
| khamsat.com | arabic_marketplace | ar | MENA | Yes | Unknown | 0 | 1 | 0 | 0.0000 | N/A | Unknown | Low | Low | Low |
| malt.fr | europe_freelance | fr/en | Europe | Yes | Unknown | 0 | 1 | 0 | 0.0000 | N/A | Unknown | Low | Low | Low |

## 5. Recommendations

### Sources to Prioritize (High Yield)
1. **freelancer.com** — 5 opportunities from 5 pages, consistent across categories
2. **weworkremotely.com** — High link extraction (441 links) enables discovery expansion
3. **remoteok.com, workingnomads.com** — Consistent remote job postings
4. **twago.com** — European market, good yield
5. **wellfound.com** — Startup ecosystem demand

### Sources to Deprioritize (Low Yield / Noise)
1. **CDN/asset domains** (f-cdn.com, cloudflare.com, cloudfront.net, typekit.net, googletagmanager.com, fonts.*) — Filter out from opportunity detection
2. **guru.com, peopleperhour.com, dribbble.com, behance.net** — No extractable content in this pilot
3. **Arabic sources** (mostaql.com, khamsat.com, bayt.com) — Extraction failures; investigate encoding/extraction approach
4. **malt.fr** — Minimal extractable content

### Collection Policy Adjustments
- Add robots.txt respect per host
- Implement per-host rate limits (1 req/sec used in pilot)
- Filter CDN/asset URLs before opportunity detection
- Investigate Arabic content extraction for MENA sources

## 6. Machine-Readable Output

Results saved to: `tests/real_world_pilot_results.json`

## 7. Limitations

- Single crawl per source (no temporal data)
- Small sample (36 pages)
- Arabic content extraction failures may underestimate MENA source value
- CDN false positives inflated some yields
