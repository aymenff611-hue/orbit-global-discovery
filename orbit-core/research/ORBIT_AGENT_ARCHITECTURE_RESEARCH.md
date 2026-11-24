# ORBIT Agent Architecture Research

**Version:** 0.1.0  
**Status:** Completed

---

## 1. Research Objective

Research agent orchestration architectures for ORBIT — deep research agents, multi-agent coordination, and workflow orchestration — without confusing research agents with crawlers.

---

## 2. Key Finding: Research Agents vs. Crawlers

ORBIT's research confirmed a critical distinction:

| Research Agents | Crawlers |
|-----------------|----------|
| Investigate and reason about specific topics | Fetch pages at scale |
| Deep, narrow exploration | Broad, shallow discovery |
| LLM-driven reasoning | HTTP-driven fetching |
| Few pages, deep analysis | Many pages, surface extraction |
| For important opportunities | For all discovered sources |

**ORBIT does not assume that a research agent is a crawler, or that a coding agent is an operational discovery engine.**

---

## 3. Candidate Agent Systems Evaluated

| System | License | Purpose | Selected? | Reason |
|--------|---------|---------|-----------|--------|
| NVIDIA AI-Q | Unknown | AI agent framework | Evaluated | Agent architecture research only |
| DeerFlow | Unknown | Deep research agent | Evaluated | Agent architecture research only |
| MiroThinker | Unknown | Agent reasoning | Evaluated | Agent architecture research only |
| Temporal | Apache-2.0 | Workflow orchestration | No | Over-engineered for ORBIT |
| Prefect | Apache-2.0 | Workflow orchestration | No | Over-engineered |
| Airflow | Apache-2.0 | Batch orchestration | No | Not for real-time discovery |
| Celery | BSD | Task queue | Yes | Simple, Python-native, sufficient |

---

## 4. ORBIT Agent Architecture

ORBIT implements a tiered model-and-agent architecture:

### Tier 1: Deterministic filters and rules
No LLM. Keyword matching, pattern matching, rule-based filtering.

### Tier 2: Lightweight classifiers
scikit-learn models. Statistical classification, low latency.

### Tier 3: Specialized extraction models
spaCy/Stanza NER. Entity extraction for organizations, budgets, dates.

### Tier 4: Larger reasoning models
LLMs for ambiguous or high-value cases. Only when Tiers 1-3 produce uncertainty.

### Tier 5: Deep research agents
Agent-based investigation for important opportunities. Multi-step research, validation, and evidence gathering.

---

## 5. Workflow Orchestration

ORBIT uses a custom workflow manager (`core/workflow.py`) with:
- Checkpointing for recovery
- Retry policies with exponential backoff
- Dead-letter handling
- Worker failure recovery
- Idempotency

Celery is used for distributed task execution.

---

## 6. Findings

- Research agents are for deep investigation of specific opportunities, not for crawling
- Crawlers are for broad discovery, not for deep reasoning
- ORBIT separates these concerns: crawlers discover, agents investigate
- Workflow orchestration is needed for recovery and checkpointing, not for the discovery logic itself
- Celery is sufficient for ORBIT's distributed task needs; Temporal/Prefect/Airflow are over-engineered

---

## 7. Integration Recommendation

- Custom workflow manager: Native ORBIT component (implemented)
- Celery: Distributed task execution adapter
- Deep research agents: Planned for Tier 5 (not yet integrated)
- NVIDIA AI-Q, DeerFlow, MiroThinker: Evaluated, not integrated

---

**End of ORBIT Agent Architecture Research**
