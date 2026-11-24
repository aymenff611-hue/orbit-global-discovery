"""ORBIT Knowledge Graph.

Stores entities and relationships with provenance evidence.
Supports temporal relationships, historical changes, and evidence tracking.
"""

import logging
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from uuid import UUID
from collections import defaultdict

from core.models import Entity, Relationship, utc_now

logger = logging.getLogger("orbit.graph.knowledge_graph")


class KnowledgeGraph:
    """In-memory knowledge graph with provenance tracking.

    Stores:
    - Entities (organizations, persons, products, services, communities, websites, opportunities)
    - Relationships between entities with provenance and evidence
    - Temporal relationships (valid_from, valid_to)
    - Historical changes
    """

    def __init__(self):
        self._entities: Dict[UUID, Entity] = {}
        self._relationships: Dict[UUID, Relationship] = {}
        self._entity_index_by_name: Dict[str, Set[UUID]] = defaultdict(set)
        self._entity_index_by_type: Dict[str, Set[UUID]] = defaultdict(set)
        self._relationships_by_source: Dict[UUID, Set[UUID]] = defaultdict(set)
        self._relationships_by_target: Dict[UUID, Set[UUID]] = defaultdict(set)
        self._relationships_by_type: Dict[str, Set[UUID]] = defaultdict(set)

        self._stats = {
            "entities": 0,
            "relationships": 0,
            "entity_types": {},
            "relationship_types": {},
        }

    def add_entity(self, entity: Entity) -> Entity:
        """Add or update an entity in the knowledge graph."""
        self._entities[entity.id] = entity
        self._entity_index_by_type[entity.entity_type].add(entity.id)
        self._entity_index_by_name[entity.name.lower()].add(entity.id)

        # Also index by canonical name
        if entity.canonical_name:
            self._entity_index_by_name[entity.canonical_name.lower()].add(entity.id)

        self._stats["entities"] = len(self._entities)
        self._stats["entity_types"][entity.entity_type] = \
            self._stats["entity_types"].get(entity.entity_type, 0) + 1

        logger.debug(f"Added entity: {entity.name} ({entity.entity_type})")
        return entity

    def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def find_entities_by_name(self, name: str) -> List[Entity]:
        """Find entities by name (case-insensitive)."""
        ids = self._entity_index_by_name.get(name.lower(), set())
        return [self._entities[eid] for eid in ids if eid in self._entities]

    def find_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Find all entities of a given type."""
        ids = self._entity_index_by_type.get(entity_type, set())
        return [self._entities[eid] for eid in ids if eid in self._entities]

    def add_relationship(self, relationship: Relationship) -> Relationship:
        """Add a relationship between two entities."""
        # Verify entities exist
        if relationship.source_entity_id not in self._entities:
            logger.warning(f"Source entity {relationship.source_entity_id} not found")
        if relationship.target_entity_id not in self._entities:
            logger.warning(f"Target entity {relationship.target_entity_id} not found")

        self._relationships[relationship.id] = relationship
        self._relationships_by_source[relationship.source_entity_id].add(relationship.id)
        self._relationships_by_target[relationship.target_entity_id].add(relationship.id)
        self._relationships_by_type[relationship.relationship_type].add(relationship.id)

        self._stats["relationships"] = len(self._relationships)
        self._stats["relationship_types"][relationship.relationship_type] = \
            self._stats["relationship_types"].get(relationship.relationship_type, 0) + 1

        logger.debug(f"Added relationship: {relationship.relationship_type} "
                     f"({relationship.source_entity_id} -> {relationship.target_entity_id})")
        return relationship

    def get_relationship(self, relationship_id: UUID) -> Optional[Relationship]:
        """Get a relationship by ID."""
        return self._relationships.get(relationship_id)

    def get_relationships_for_entity(self, entity_id: UUID,
                                     direction: str = "both") -> List[Relationship]:
        """Get all relationships for an entity.

        Args:
            entity_id: The entity to find relationships for
            direction: "outgoing", "incoming", or "both"
        """
        result: Set[UUID] = set()

        if direction in ("outgoing", "both"):
            result.update(self._relationships_by_source.get(entity_id, set()))
        if direction in ("incoming", "both"):
            result.update(self._relationships_by_target.get(entity_id, set()))

        return [self._relationships[rid] for rid in result if rid in self._relationships]

    def get_relationships_by_type(self, relationship_type: str) -> List[Relationship]:
        """Get all relationships of a given type."""
        ids = self._relationships_by_type.get(relationship_type, set())
        return [self._relationships[rid] for rid in ids if rid in self._relationships]

    def resolve_entity(self, name: str, entity_type: Optional[str] = None,
                       attributes: Optional[Dict[str, Any]] = None) -> Optional[Entity]:
        """Attempt to resolve an entity by name and type.

        This is a basic resolution - production would use more sophisticated
        entity resolution (fuzzy matching, blocking, ML-based matching).
        """
        candidates = self.find_entities_by_name(name)

        if entity_type:
            candidates = [e for e in candidates if e.entity_type == entity_type]

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # Multiple candidates - try to match by attributes
        if attributes:
            for entity in candidates:
                match = True
                for key, value in attributes.items():
                    if entity.attributes.get(key) != value:
                        match = False
                        break
                if match:
                    return entity

        # Return the most recently updated
        return max(candidates, key=lambda e: e.updated_at)

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        return {
            **self._stats,
            "entities_by_type": dict(self._stats["entity_types"]),
            "relationships_by_type": dict(self._stats["relationship_types"]),
        }

    def export_graph(self) -> Dict[str, Any]:
        """Export the entire graph as a dictionary."""
        return {
            "entities": [
                {
                    "id": str(e.id),
                    "type": e.entity_type,
                    "name": e.name,
                    "canonical_name": e.canonical_name,
                    "attributes": e.attributes,
                }
                for e in self._entities.values()
            ],
            "relationships": [
                {
                    "id": str(r.id),
                    "source": str(r.source_entity_id),
                    "target": str(r.target_entity_id),
                    "type": r.relationship_type,
                    "properties": r.properties,
                    "confidence": r.confidence,
                }
                for r in self._relationships.values()
            ],
        }
