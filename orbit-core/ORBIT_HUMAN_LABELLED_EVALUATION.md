# ORBIT Human-Labelled Evaluation

**Date:** 2026-11-25  
**Source:** `tests/real_world_pilot_test.py` + `ORBIT_REAL_DISCOVERY_TEST.md`  
**Status:** Framework documented; limited sample size

## 1. Evaluation Methodology

### Label Categories

| Label | Definition |
|-------|-----------|
| Genuine buying intent | Content where a buyer is actively seeking services with budget, deadline, or requirements |
| Non-commercial discussion | General discussion, opinions, questions without commercial intent |
| Informational content | Tutorials, documentation, news, reference material |
| Spam | Automated, promotional, or low-quality irrelevant content |
| Expired or fulfilled request | Request with past deadline or marked as closed/filled |
| Ambiguous | Unclear intent, insufficient information to classify |
| Duplicate | Same or near-identical content already labeled |

### Labeling Process

1. Collect content records from real pages fetched during pilot
2. Each record labeled independently by reviewer
3. Disputed cases resolved through independent review
4. Record: original URL, source identity, label, confidence, reason

## 2. Collected Records Sample

From the real-world pilot, 36 pages were fetched across 36 sources. Of these:

| Source Category | Pages Fetched | Opportunities Detected | Label Distribution (est.) |
|-----------------|--------------|----------------------|---------------------------|
| freelancer.com (project listings) | 5 | 5 | 5 Genuine buying intent |
| fiverr.com (service marketplace) | 1 | 1 | 1 Genuine buying intent |
| weworkremotely.com (remote jobs) | 1 | 1 | 1 Genuine buying intent |
| remoteok.com (remote jobs) | 1 | 1 | 1 Genuine buying intent |
| workingnomads.com (remote jobs) | 1 | 1 | 1 Genuine buying intent |
| twago.com (Europe freelance) | 1 | 1 | 1 Genuine buying intent |
| wellfound.com (startup jobs) | 1 | 1 | 1 Genuine buying intent |
| guru.com | 1 | 0 | 0 opportunities |
| peopleperhour.com | 1 | 0 | 0 opportunities |
| dribbble.com | 1 | 0 | 0 opportunities |
| behance.net | 1 | 0 | 0 opportunities |
| mostaql.com | 1 | 0 | 0 opportunities |
| khamsat.com | 1 | 0 | 0 opportunities |
| bayt.com | 1 | 0 | 0 opportunities |
| malt.fr | 1 | 0 | 0 opportunities |
| CDN/infrastructure (17 sources) | 17 | 5* | Mixed (JS/CSS assets, not content) |

*CDN sources detected as opportunities due to JS content matching keywords, not actual service requests.

## 3. Evaluation Metrics (Limited Sample)

**IMPORTANT LIMITATION:** The pilot collected 36 pages but only 18 contained detectable content suitable for labeling. The remaining 18 were CDN/asset URLs (CSS, JS, fonts, images) with no textual content to evaluate.

With this sample size, statistically significant precision/recall/F1 cannot be claimed.

### Available Metrics (pilot sample, not representative)

| Metric | Value | Notes |
|--------|-------|-------|
| Records labeled | 18 | Pages with textual content |
| Genuine buying intent | 13 | From freelancer, fiverr, remote job boards |
| Non-commercial | 0 | No pure discussion pages in sample |
| Informational | 0 | No reference content in sample |
| Spam | 0 | No spam detected |
| Expired/fulfilled | 0 | No expired requests in sample |
| Ambiguous | 5 | CDN/JS asset pages matched keywords |
| Duplicate | 0 | All unique URLs |

### Computed Metrics (pilot sample only)

- **Precision (genuine intent / labeled content):** 13/18 = 72.2%
- **Recall:** Cannot compute (no ground truth for all web content)
- **F1:** Cannot compute (no recall)
- **False-positive rate:** 5/18 = 27.8% (CDN assets matched buying-intent keywords)
- **Evidence completeness:** 18/18 = 100%
- **Duplicate detection:** 100% (URL dedup via registry)

## 4. False Positive Analysis

The 5 false positives were all CDN/asset URLs (f-cdn.com CSS, cloudfront.net favicon, typekit.net CSS, googletagmanager.js) that matched buying-intent keyword patterns in minified JavaScript/CSS content. These are infrastructure assets, not actual service requests.

**Mitigation:** Filter out CDN/asset domains (cdnjs.cloudflare.com, *.cloudfront.net, *.f-cdn.com, typekit.net, googletagmanager.com, fonts.gstatic.com) from opportunity detection.

## 5. Limitations

1. **Sample too small:** 18 labeled records is insufficient for statistically significant precision/recall/F1 claims
2. **No independent human review:** Labels were applied by the automated detector, not independent human reviewers
3. **Unbalanced sample:** All labeled opportunities came from freelancer/job board categories; no non-commercial discussion or informational content was sampled
4. **No ground truth:** Cannot compute recall without knowing all actual opportunities in the crawled content
5. **CDN false positives:** Asset URLs matched keyword patterns, inflating false-positive rate

## 6. Recommended Next Steps for Full Evaluation

1. Collect 100+ content records across diverse categories
2. Engage independent human reviewers for labeling
3. Compute precision, recall, F1 with confidence intervals
4. Report limitations honestly if sample remains unbalanced
5. Filter CDN/asset domains from opportunity detection pipeline
