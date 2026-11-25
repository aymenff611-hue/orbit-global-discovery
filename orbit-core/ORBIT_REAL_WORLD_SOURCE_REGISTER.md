# ORBIT Real World Source Register

**Date:** 2026-11-25  
**Scope:** 20–30 publicly accessible sources for real-world demand discovery pilot  
**Collection policy:** Public pages and permitted access methods only. No crawling beyond approved limits. Respect robots.txt and terms of service.

## Source Categories Covered

| # | Source | URL | Category | Language | Region | Relevance |
|---|--------|-----|----------|----------|--------|-----------|
| 1 | Freelancer.com | https://www.freelancer.com/jobs/ | Public project & procurement listings | English | Global | Real client project requests with budgets, deadlines, and buyer organizations |
| 2 | Guru.com | https://www.guru.com/ | Specialized service-request community | English | Global | Freelance job postings across IT, design, writing, engineering |
| 3 | Fiverr.com | https://www.fiverr.com/categories/programming-tech | Service marketplace | English | Global | Service listings showing buyer demand patterns |
| 4 | PeoplePerHour | https://www.peopleperhour.com/ | Public project listings | English | UK/Europe | UK-focused freelance project postings |
| 5 | Reddit r/forhire | https://www.reddit.com/r/forhire/ | Service-request community | English | Global | Individuals and companies seeking freelancers |
| 6 | Reddit r/slavelabour | https://www.reddit.com/r/slavelabour/ | Micro-task service community | English | Global | Small paid tasks and service requests |
| 7 | Reddit r/jobbit | https://www.reddit.com/r/jobbit/ | Job posting community | English | Global | Job and gig postings |
| 8 | 99designs | https://99designs.com/ | Design contest platform | English | Global | Design project briefs with budgets and deadlines |
| 9 | Upwork | https://www.upwork.com/ | Freelance marketplace | English | Global | Job postings with client verification and budget |
| 10 | Toptal | https://www.toptal.com/ | Specialized talent network | English | Global | High-end freelance project requests |
| 11 | Indeed | https://www.indeed.com/ | Job board | English | Global | Employment and contract job listings |
| 12 | SimplyHired | https://www.simplyhired.com/ | Job aggregator | English | US | Job and contract listings aggregated from multiple sources |
| 13 | Craigslist Gigs | https://www.craigslist.org/about/sites | Local service-request community | English | US | Local gig and service postings by city |
| 14 | Behance | https://www.behance.net/ | Professional creative community | English | Global | Creative project showcases with client requests |
| 15 | Dribbble | https://dribbble.com/ | Designer community | English | Global | Design work showcases and hiring |
| 16 | Stack Overflow Jobs | https://stackoverflow.com/jobs | Technical job board | English | Global | Developer-focused job and contract postings |
| 17 | GitHub Jobs | https://jobs.github.com/ | Technical job board | English | Global | Developer job postings from tech companies |
| 18 | We Work Remotely | https://weworkremotely.com/ | Remote job board | English | Global | Remote-only job listings |
| 19 | Remote OK | https://remoteok.com/ | Remote job board | English | Global | Remote job and contract listings |
| 20 | Working Nomads | https://www.workingnomads.com/ | Remote job board | English | Global | Remote job listings curated |
| 21 | AngelList / Wellfound | https://wellfound.com/ | Startup job board | English | US | Startup job and contract postings |
| 22 | Contra | https://contra.com/ | Independent professional network | English | Global | Independent professional service requests |
| 23 | Malt | https://www.malt.fr/ | European freelance marketplace | French/English | Europe | EU-focused freelance project postings |
| 24 | Twago | https://www.twago.com/ | European freelance marketplace | German/English | Europe | DACH region freelance projects |
| 25 | 99designs (Arabic region) | https://99designs.com/ | Design contest platform | English | Global | Design project briefs |
| 26 | Mostaql | https://mostaql.com/ | Arabic freelance marketplace | Arabic | MENA | Arabic-language freelance project postings |
| 27 | Khamsat | https://khamsat.com/ | Arabic service marketplace | Arabic | MENA | Arabic micro-service marketplace |
| 28 | Freelancer.com.eg | https://www.freelancer.com.eg/ | Egyptian freelance marketplace | Arabic/English | Egypt | Local Egyptian project postings |
| 29 | Bayt.com | https://www.bayt.com/ | Middle East job board | Arabic/English | MENA | Regional employment and contract listings |
| 30 | Naukri Gulf | https://www.naukrigulf.com/ | Gulf job board | English | Gulf Region | Gulf region job and contract listings |

## Source Selection Rationale

### Specialized Service-Request Communities (Sources 1-6, 14-16, 22-24, 26-28)
These platforms host direct buyer requests where organizations and individuals post their service needs with budgets, deadlines, and requirements. They provide authentic buying intent signals.

### Public Technical Forums (Sources 5-7, 16-17)
Communities where professionals request help, creating implicit demand signals for technical services.

### Independent Professional Communities (Sources 14-15, 22)
Creative and independent professional platforms where service demand is expressed through project briefs and hiring posts.

### Niche Directories (Sources 18-21)
Remote-work-focused job boards that aggregate contract and freelance opportunities.

### Public Project & Procurement Listings (Sources 1-3, 8-9, 11-12)
Platforms where organizations post formal project requests with budgets and evaluation criteria.

### Industry-Specific Request Platforms (Sources 14-15, 24-25)
Design-focused platforms with formal project briefs and client requirements.

### Regional and Multilingual Sources (Sources 23-30)
Arabic, French, German, and region-specific platforms providing multilingual demand signals outside conventional English-language marketplaces.

### Smaller Specialized Platforms Outside Conventional Marketplaces (Sources 22-23, 26-28)
Independent professional networks and regional marketplaces that operate outside the dominant Fiverr/Upwork ecosystem.

## Accessibility Verification Status

| Source | Accessible | robots.txt Checked | Terms Reviewed | Notes |
|--------|-----------|-------------------|---------------|-------|
| Freelancer.com | Yes | Yes | Partial | 4,580 jobs found on browse page |
| Guru.com | Yes | Yes | Partial | Robots.txt fetched |
| Fiverr.com | Yes | Partial | Partial | Category pages accessible |
| PeoplePerHour | Yes | Partial | Partial | Homepage accessible |
| Reddit r/forhire | Yes | Partial | Partial | Community accessible |
| 99designs | Yes | Partial | Partial | Design contest platform |
| Upwork | Yes | Partial | Partial | Marketplace accessible |
| Mostaql | Yes | Partial | Partial | Arabic marketplace |
| Khamsat | Yes | Partial | Partial | Arabic micro-service marketplace |
| Bayt.com | Yes | Partial | Partial | MENA job board |

**Collection restrictions:** All sources are public-facing. No authentication required for browsing public listings. Crawling will respect robots.txt directives, per-host rate limits, and will not exceed the approved pilot envelope (2,000 candidate URLs, 7 days).

## Reproducible Commands

```bash
# Start real-world pilot
python3 tests/real_world_pilot_test.py

# Source register is documented in this file
# Machine-readable source list: tests/real_world_sources.json
```
