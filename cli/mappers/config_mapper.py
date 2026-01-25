"""YAML-driven field mapper - no Python coding required."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from cli.mappers.base import FieldMapper


# Minimal required fields for lenient mode
MINIMAL_REQUIRED = ["event_ts", "event_type"]


class ConfigMapper(FieldMapper):
    """YAML-driven mapper that loads field mappings from config files.

    Config format:
        source: firewall
        description: "Palo Alto firewall syslog exports"

        field_map:
          receive_time: event_ts
          src: src_ip
          dst: dest_ip

        defaults:
          event_type: "network_flow"
          source_system: "palo_alto"

        required_only:
          - event_ts
          - event_type

        transforms:
          event_ts:
            format: "%Y/%m/%d %H:%M:%S"
          bytes_out:
            type: int
    """

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = yaml.safe_load(config_path.read_text())
        self._field_map = self.config.get("field_map", {})
        self.defaults = self.config.get("defaults", {})
        self.required_fields = self.config.get("required_only", MINIMAL_REQUIRED)
        self.transforms = self.config.get("transforms", {})
        self._source = self.config.get("source", config_path.stem)
        self._description = self.config.get("description", "")

    @property
    def field_map(self) -> Dict[str, str]:
        return self._field_map

    @property
    def source_name(self) -> str:
        return self._source

    @property
    def description(self) -> str:
        return self._description

    def transform_value(self, unified_field: str, value: Any) -> Any:
        """Apply transforms defined in config."""
        transform = self.transforms.get(unified_field)
        if not transform or value is None:
            return value

        # Type coercion
        type_name = transform.get("type")
        if type_name:
            try:
                if type_name == "int":
                    return int(value)
                elif type_name == "float":
                    return float(value)
                elif type_name == "str":
                    return str(value)
                elif type_name == "bool":
                    return str(value).lower() in ("true", "1", "yes")
            except (ValueError, TypeError):
                return value

        # Datetime parsing
        fmt = transform.get("format")
        if fmt and unified_field == "event_ts":
            try:
                dt = datetime.strptime(str(value), fmt)
                return dt.isoformat() + "Z"
            except ValueError:
                pass

        return value

    def post_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Apply defaults for missing fields."""
        for field, value in self.defaults.items():
            if field not in row or row[field] is None:
                row[field] = value
        return row

    def get_required_fields(self) -> List[str]:
        """Return the required fields for validation."""
        return self.required_fields


def load_config_mapper(config_path: Path) -> Optional[ConfigMapper]:
    """Load a ConfigMapper from a YAML file, returning None if invalid."""
    try:
        return ConfigMapper(config_path)
    except (yaml.YAMLError, OSError):
        # Log warning but don't fail - fall back to other mappers
        return None
