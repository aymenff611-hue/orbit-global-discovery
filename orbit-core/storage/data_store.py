"""ORBIT Data Store.

Manages hot/warm/cold storage lifecycle with compression, deduplication,
retention policies, and archival strategies.
"""

import logging
import os
import json
import gzip
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("orbit.storage.data_store")


class StorageTier(str, Enum):
    HOT = "hot"       # Active operational data (fast access, expensive)
    WARM = "warm"     # Recent content and searchable evidence
    COLD = "cold"     # Historical archives (object storage, cheap)


@dataclass
class StoredContent:
    """A piece of stored content with metadata."""
    content_id: str
    url: str
    content_type: str  # raw, extracted, structured
    tier: StorageTier
    size_bytes: int
    compressed: bool
    checksum: str
    storage_path: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataStore:
    """Manages data lifecycle across hot/warm/cold storage tiers.

    Design principles:
    - Hot storage for active operational data (recent, frequently accessed)
    - Warm storage for recent content and searchable evidence
    - Cold/object storage for historical archives
    - Configurable retention and deletion policies
    - Compression and deduplication
    - Separate raw content from extracted text and structured records
    """

    def __init__(self, settings=None):
        self.settings = settings
        self.hot_path = settings.storage_hot_path if settings else "/data/orbit/hot"
        self.warm_path = settings.storage_warm_path if settings else "/data/orbit/warm"
        self.cold_path = settings.storage_cold_path if settings else "/data/orbit/cold"
        self.compression_enabled = settings.storage_compression_enabled if settings else True
        self.deduplication_enabled = settings.storage_deduplication_enabled if settings else True

        self.hot_retention_days = settings.storage_hot_retention_days if settings else 30
        self.warm_retention_days = settings.storage_warm_retention_days if settings else 365
        self.cold_retention_days = settings.storage_cold_retention_days if settings else 2555

        # In-memory index (production would use a database)
        self._index: Dict[str, StoredContent] = {}
        self._checksum_index: Dict[str, str] = {}  # checksum -> content_id (dedup)

        self._stats = {
            "stored_items": 0,
            "hot_items": 0,
            "warm_items": 0,
            "cold_items": 0,
            "total_bytes": 0,
            "compressed_bytes_saved": 0,
            "duplicates_rejected": 0,
        }

        # Create directories
        for path in [self.hot_path, self.warm_path, self.cold_path]:
            os.makedirs(path, exist_ok=True)

    def store(self, content_id: str, url: str, content: bytes,
              content_type: str = "raw",
              tier: StorageTier = StorageTier.HOT,
              source_id: Optional[str] = None,
              metadata: Optional[Dict[str, Any]] = None) -> StoredContent:
        """Store content in the appropriate tier."""
        # Check deduplication
        import hashlib
        checksum = hashlib.sha256(content).hexdigest()

        if self.deduplication_enabled and checksum in self._checksum_index:
            existing_id = self._checksum_index[checksum]
            self._stats["duplicates_rejected"] += 1
            logger.debug(f"Duplicate content rejected: {content_id} -> {existing_id}")
            return self._index[existing_id]

        # Compress if enabled
        compressed = False
        data_to_store = content
        if self.compression_enabled and len(content) > 1024:
            data_to_store = gzip.compress(content)
            compressed = True
            self._stats["compressed_bytes_saved"] += len(content) - len(data_to_store)

        # Determine storage path
        storage_path = self._get_storage_path(tier, content_id)

        # Write to disk
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(data_to_store)

        # Calculate expiration
        expires_at = None
        if tier == StorageTier.HOT:
            expires_at = datetime.now(timezone.utc) + timedelta(days=self.hot_retention_days)
        elif tier == StorageTier.WARM:
            expires_at = datetime.now(timezone.utc) + timedelta(days=self.warm_retention_days)
        elif tier == StorageTier.COLD:
            expires_at = datetime.now(timezone.utc) + timedelta(days=self.cold_retention_days)

        stored = StoredContent(
            content_id=content_id,
            url=url,
            content_type=content_type,
            tier=tier,
            size_bytes=len(content),
            compressed=compressed,
            checksum=checksum,
            storage_path=storage_path,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            source_id=source_id,
            metadata=metadata or {},
        )

        self._index[content_id] = stored
        if self.deduplication_enabled:
            self._checksum_index[checksum] = content_id

        self._stats["stored_items"] += 1
        self._stats["total_bytes"] += len(content)
        self._update_tier_stats()

        logger.debug(f"Stored {content_type} content {content_id} in {tier.value} tier ({len(content)} bytes)")
        return stored

    def retrieve(self, content_id: str) -> Optional[bytes]:
        """Retrieve content by ID."""
        stored = self._index.get(content_id)
        if not stored:
            logger.warning(f"Content {content_id} not found")
            return None

        # Check expiration
        if stored.expires_at and datetime.now(timezone.utc) > stored.expires_at:
            logger.warning(f"Content {content_id} has expired")
            return None

        # Read from disk
        try:
            with open(stored.storage_path, "rb") as f:
                data = f.read()

            # Decompress if needed
            if stored.compressed:
                data = gzip.decompress(data)

            # Update access stats
            stored.last_accessed = datetime.now(timezone.utc)
            stored.access_count += 1

            return data
        except FileNotFoundError:
            logger.error(f"Storage file not found: {stored.storage_path}")
            return None

    def delete(self, content_id: str) -> bool:
        """Delete content by ID."""
        stored = self._index.get(content_id)
        if not stored:
            return False

        # Delete file
        try:
            if os.path.exists(stored.storage_path):
                os.remove(stored.storage_path)
        except OSError as e:
            logger.error(f"Failed to delete file {stored.storage_path}: {e}")

        # Remove from index
        if stored.checksum in self._checksum_index:
            del self._checksum_index[stored.checksum]
        del self._index[content_id]

        self._stats["stored_items"] -= 1
        self._stats["total_bytes"] -= stored.size_bytes
        self._update_tier_stats()

        logger.debug(f"Deleted content {content_id}")
        return True

    def move_to_tier(self, content_id: str, new_tier: StorageTier) -> bool:
        """Move content between storage tiers."""
        stored = self._index.get(content_id)
        if not stored:
            return False

        if stored.tier == new_tier:
            return True

        # Read data
        data = self.retrieve(content_id)
        if data is None:
            return False

        # Delete old
        self.delete(content_id)

        # Store in new tier
        new_expires = None
        if new_tier == StorageTier.HOT:
            new_expires = datetime.now(timezone.utc) + timedelta(days=self.hot_retention_days)
        elif new_tier == StorageTier.WARM:
            new_expires = datetime.now(timezone.utc) + timedelta(days=self.warm_retention_days)
        elif new_tier == StorageTier.COLD:
            new_expires = datetime.now(timezone.utc) + timedelta(days=self.cold_retention_days)

        stored.tier = new_tier
        stored.storage_path = self._get_storage_path(new_tier, content_id)
        stored.expires_at = new_expires

        # Write to new location
        data_to_store = data
        compressed = False
        if self.compression_enabled and len(data) > 1024:
            data_to_store = gzip.compress(data)
            compressed = True

        os.makedirs(os.path.dirname(stored.storage_path), exist_ok=True)
        with open(stored.storage_path, "wb") as f:
            f.write(data_to_store)

        stored.compressed = compressed
        self._index[content_id] = stored
        self._update_tier_stats()

        logger.info(f"Moved {content_id} from {stored.tier.value} to {new_tier.value}")
        return True

    def run_retention_policy(self) -> Dict[str, int]:
        """Run retention policy: delete expired content and move old content between tiers.

        Returns statistics about actions taken.
        """
        now = datetime.now(timezone.utc)
        actions = {"deleted": 0, "moved_to_warm": 0, "moved_to_cold": 0}

        # Find expired content
        expired_ids = [
            cid for cid, stored in self._index.items()
            if stored.expires_at and now > stored.expires_at
        ]

        for cid in expired_ids:
            self.delete(cid)
            actions["deleted"] += 1

        # Move hot -> warm (content older than hot retention but not expired)
        warm_cutoff = now - timedelta(days=self.hot_retention_days // 2)
        for cid, stored in list(self._index.items()):
            if stored.tier == StorageTier.HOT and stored.created_at < warm_cutoff:
                self.move_to_tier(cid, StorageTier.WARM)
                actions["moved_to_warm"] += 1

        # Move warm -> cold
        cold_cutoff = now - timedelta(days=self.warm_retention_days // 2)
        for cid, stored in list(self._index.items()):
            if stored.tier == StorageTier.WARM and stored.created_at < cold_cutoff:
                self.move_to_tier(cid, StorageTier.COLD)
                actions["moved_to_cold"] += 1

        logger.info(f"Retention policy complete: {actions}")
        return actions

    def _get_storage_path(self, tier: StorageTier, content_id: str) -> str:
        """Get the filesystem path for content."""
        base = {
            StorageTier.HOT: self.hot_path,
            StorageTier.WARM: self.warm_path,
            StorageTier.COLD: self.cold_path,
        }[tier]
        # Shard by first 2 chars of content_id
        shard = content_id[:2]
        return os.path.join(base, shard, f"{content_id}.dat")

    def _update_tier_stats(self):
        """Update per-tier statistics."""
        self._stats["hot_items"] = sum(1 for s in self._index.values() if s.tier == StorageTier.HOT)
        self._stats["warm_items"] = sum(1 for s in self._index.values() if s.tier == StorageTier.WARM)
        self._stats["cold_items"] = sum(1 for s in self._index.values() if s.tier == StorageTier.COLD)

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return dict(self._stats)

    def get_content(self, content_id: str) -> Optional[StoredContent]:
        """Get content metadata."""
        return self._index.get(content_id)
