# ORBIT Source Discovery Research

**Version:** 0.1.0  
**Status:** Completed

---

## 1. Research Objective

Research the best technologies and methods for global source discovery — discovering up to 1 billion candidate URLs per day, processing 1 million candidate sources, and validating 10,000 new useful sources per day.

---

## 2. Discovery Methods Evaluated

| Method | Description | Candidates | Selected |
|--------|-------------|------------|----------|
| Web graph relationships | Following links between pages | Common Crawl, web graphs | Common Crawl index |
| Sitemaps | XML sitemaps from websites | Custom parser | Custom implementation |
| RSS/Atom feeds | Syndication feeds | Custom parser | Custom implementation |
| Public directories | Business and service directories | Manual curation | Custom implementation |
| Search interfaces | Public search engine APIs | Google, Bing, DuckDuckGo | Not integrated (TOS restrictions) |
| Public datasets | Open data portals | data.gov, EU open data | Custom adapters |
| DNS intelligence | DNS records, zone files | DNS resolvers | Custom implementation |
| Certificate transparency | CT logs | crt.sh, Google CT | Custom implementation |
| Community indexes | Forum indexes, community lists | Manual curation | Custom implementation |
| Marketplace listings | Public marketplace listings | Manual curation | Custom implementation |
| References from sources | Sources referencing other sources | Recursive discovery | Recursive discovery engine |
| Industry associations | Trade associations, chambers | Manual curation | Custom implementation |
| Regional discovery | Country-specific sources | Regional curators | Custom implementation |

---

## 3. Candidate Technologies

| Technology | License | Maintenance | Scalability | Selected? | Reason |
|------------|---------|-------------|-------------|-----------|--------|
| Common Crawl | Public domain | Active | Petabyte-scale | Yes | Free web crawl data, URL index |
| Apache Nutch | Apache-2.0 | Moderate | High | No | Too heavy, complex operations |
| Common Crawl URL Index | Public domain | Active | Billions of URLs | Yes | URL discovery at scale |
| Certificate Transparency logs | Public | Active | Millions of certs | Yes | Domain discovery |
| DNS zone files | Various | Active | Millions of domains | Yes | Domain discovery |

---

## 4. Source Classification

ORBIT distinguishes between:

1. **Candidate URLs** — URLs discovered but not yet evaluated
2. **Candidate Domains** — Domains extracted from candidate URLs
3. **Validated Domains** — Domains verified as accessible and relevant
4. **Useful Sources** — Sources that produce useful content
5. **Active Monitored Sources** — Sources actively being crawled
6. **Qualified Demand Sources** — Sources that produce qualified demand

**Never count duplicates as new discoveries.**

---

## 5. Findings

- Common Crawl provides the largest public URL index (billions of URLs)
- Certificate Transparency logs are excellent for domain discovery
- DNS zone files provide domain intelligence but require access
- Sitemaps and RSS are underutilized discovery methods
- Recursive discovery from existing sources produces the highest quality sources
- Regional and language-specific sources require dedicated curation

---

## 6. Limitations

- Common Crawl data is not real-time (monthly crawls)
- Search engine APIs have TOS restrictions on automated scraping
- Many niche directories require authentication
- Regional sources may be in languages with limited NLP support

---

## 7. Integration Recommendation

- Common Crawl URL index: Direct integration for URL discovery
- Certificate Transparency: Direct integration for domain discovery
- Sitemaps/RSS: Custom parser in discovery engine
- DNS/Zone files: Custom implementation
- Search engines: Not integrated due to TOS restrictions

---

**End of ORBIT Source Discovery Research**
