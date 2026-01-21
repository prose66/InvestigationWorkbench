"""Base field mapper interface and utilities."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class FieldMapper(ABC):
    """Abstract base class for source-specific field mappers."""

    @property
    @abstractmethod
    def field_map(self) -> Dict[str, str]:
        """Map of source field names to unified schema field names.
        
        Keys are source field names (case-insensitive matching supported).
        Values are unified schema field names.
        """
        pass

    @property
    def source_name(self) -> str:
        """Human-readable name for this source type."""
        return self.__class__.__name__.replace("Mapper", "")

    def transform_value(self, unified_field: str, value: Any) -> Any:
        """Transform a value after mapping. Override for custom transforms."""
        return value

    def pre_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-process row before field mapping. Override for source-specific logic."""
        return row

    def post_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process row after field mapping. Override for derived fields."""
        return row

    def map_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map a source row to unified schema fields."""
        row = self.pre_process(row)
        result: Dict[str, Any] = {}
        source_keys_lower = {k.lower(): k for k in row.keys()}

        # First pass: copy fields that already match unified schema
        for key, value in row.items():
            result[key] = value

        # Second pass: apply field mappings (source -> unified)
        for source_field, unified_field in self.field_map.items():
            source_key = source_keys_lower.get(source_field.lower())
            if source_key and row.get(source_key) is not None:
                value = row[source_key]
                transformed = self.transform_value(unified_field, value)
                if transformed is not None:
                    result[unified_field] = transformed

        result = self.post_process(result)
        return result


def apply_mapper(mapper: FieldMapper, row: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a field mapper to a row."""
    return mapper.map_row(row)
