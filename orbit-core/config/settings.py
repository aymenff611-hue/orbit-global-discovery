"""ORBIT Core configuration system.

All configuration is environment-variable driven with sensible defaults.
No hardcoded service categories, industries, countries, or commercial offers.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional, Dict, Any
import os


class ORBITSettings(BaseSettings):
    """Core ORBIT configuration. Extendable per deployment."""

    # === System identity ===
    instance_name: str = Field(default="orbit-core", description="ORBIT instance identifier")
    instance_id: str = Field(default="orbit-001", description="Unique instance ID")

    # === API and control plane ===
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=4)
    api_version: str = Field(default="v1")
    api_secret_key: str = Field(default="orbit-dev-secret-change-in-production")

    # === Discovery configuration ===
    discovery_max_candidates_per_day: int = Field(default=1_000_000)
    discovery_max_sources_per_day: int = Field(default=1_000_000)
    discovery_max_validated_per_day: int = Field(default=10_000)
    discovery_registry_capacity: int = Field(default=100_000_000)
    discovery_seed_domains: List[str] = Field(default_factory=list)
    discovery_enable_recursive: bool = Field(default=True)
    discovery_max_generations: int = Field(default=10)
    discovery_enable_dns: bool = Field(default=True)
    discovery_enable_ct: bool = Field(default=True)  # Certificate Transparency
    discovery_enable_sitemap: bool = Field(default=True)
    discovery_enable_rss: bool = Field(default=True)

    # === Crawling configuration ===
    crawl_initial_pages_per_day: int = Field(default=100_000)
    crawl_production_pages_per_day: int = Field(default=1_000_000)
    crawl_large_pages_per_day: int = Field(default=10_000_000)
    crawl_maximum_pages_per_day: int = Field(default=100_000_000)
    crawl_max_concurrent_workers: int = Field(default=100)
    crawl_per_host_concurrency: int = Field(default=2)
    crawl_per_host_delay_seconds: float = Field(default=1.0)
    crawl_respect_robots_txt: bool = Field(default=True)
    crawl_user_agent: str = Field(
        default="ORBIT-DiscoveryBot/1.0 (+https://orbit.example.com/bot)",
        description="Identifiable user agent",
    )
    crawl_timeout_seconds: int = Field(default=30)
    crawl_max_retries: int = Field(default=5)
    crawl_backoff_base_seconds: float = Field(default=2.0)
    crawl_enable_browser_rendering: bool = Field(default=True)
    crawl_browser_max_concurrent: int = Field(default=10)
    crawl_browser_render_only_when_necessary: bool = Field(default=True)

    # === Storage configuration ===
    storage_hot_retention_days: int = Field(default=30)
    storage_warm_retention_days: int = Field(default=365)
    storage_cold_retention_days: int = Field(default=2555)  # 7 years
    storage_compression_enabled: bool = Field(default=True)
    storage_deduplication_enabled: bool = Field(default=True)
    storage_raw_path: str = Field(default="/data/orbit/raw")
    storage_extracted_path: str = Field(default="/data/orbit/extracted")
    storage_object_storage_endpoint: Optional[str] = Field(default=None)
    storage_object_storage_bucket: str = Field(default="orbit-archive")

    # === Queue configuration ===
    queue_broker_url: str = Field(default="redis://localhost:6379/0")
    queue_result_backend: str = Field(default="redis://localhost:6379/1")
    queue_enable_dead_letter: bool = Field(default=True)
    queue_max_retries: int = Field(default=5)

    # === Database ===
    database_url: str = Field(default="postgresql://orbit:orbit@localhost:5432/orbit")

    # === Search ===
    search_engine_url: str = Field(default="http://localhost:9200")
    search_index_prefix: str = Field(default="orbit")

    # === Graph ===
    graph_uri: str = Field(default="bolt://localhost:7687")
    graph_user: str = Field(default="neo4j")
    graph_password: str = Field(default="orbit-graph")

    # === Language & Geo ===
    supported_languages: List[str] = Field(default_factory=lambda: ["en", "ar", "es", "fr", "de", "zh", "ja", "ko", "ru", "pt"])
    supported_countries: List[str] = Field(default_factory=list)  # Empty = all
    language_detection_confidence_threshold: float = Field(default=0.7)

    # === Demand & Intent ===
    demand_max_events_per_day: int = Field(default=10_000_000)
    intent_precision_target: float = Field(default=0.90)
    intent_recall_target: float = Field(default=0.80)

    # === Competition ===
    competition_observable_only: bool = Field(default=True)

    # === Security ===
    security_enable_ssrf_protection: bool = Field(default=True)
    security_enable_dns_rebinding_protection: bool = Field(default=True)
    security_sandbox_browser: bool = Field(default=True)
    security_audit_log_enabled: bool = Field(default=True)

    # === Tenant isolation ===
    tenant_isolation_enabled: bool = Field(default=True)

    # === Adaptive discovery ===
    adaptive_exploration_weight: float = Field(default=0.3)
    adaptive_exploitation_weight: float = Field(default=0.7)
    adaptive_min_yield_threshold: float = Field(default=0.05)
    adaptive_rebalance_interval_seconds: int = Field(default=300)

    # === Model tiering ===
    model_tier1_lightweight: str = Field(default="rule-based")
    model_tier2_specialized: str = Field(default="small-classifier")
    model_tier3_reasoning: str = Field(default="large-reasoning-model")
    model_provider: str = Field(default="local")  # local, openai, anthropic, etc.

    class Config:
        env_prefix = "ORBIT_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = ORBITSettings()

__all__ = ["settings", "ORBITSettings"]
