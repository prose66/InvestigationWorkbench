"""Source-specific field mappers for normalizing SIEM exports to unified schema."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from cli.mappers.base import FieldMapper, apply_mapper
from cli.mappers.splunk import SplunkMapper
from cli.mappers.kusto import KustoMapper
from cli.mappers.cloudtrail import CloudTrailMapper
from cli.mappers.okta import OktaMapper
from cli.mappers.generic import GenericMapper
from cli.mappers.config_mapper import ConfigMapper, load_config_mapper

# Built-in Python mappers
BUILTIN_MAPPERS: Dict[str, type] = {
    "splunk": SplunkMapper,
    "kusto": KustoMapper,
    "cloudtrail": CloudTrailMapper,
    "aws": CloudTrailMapper,
    "okta": OktaMapper,
}

# Path to bundled YAML configs
CONFIGS_DIR = Path(__file__).parent / "configs"


def get_mapper(source: str, case_path: Optional[Path] = None) -> Tuple[FieldMapper, str]:
    """Get the appropriate mapper for a source system.

    Lookup order:
    1. Case-specific YAML config (cases/<case_id>/mappers/<source>.yaml)
    2. Global bundled YAML config (cli/mappers/configs/<source>.yaml)
    3. Built-in Python mapper
    4. Generic fallback mapper

    Args:
        source: Source system name (e.g., 'splunk', 'firewall')
        case_path: Optional path to case directory for case-specific configs

    Returns:
        Tuple of (mapper instance, mapper_type) where mapper_type is one of:
        "yaml_case", "yaml_builtin", "builtin", "generic"
    """
    source_lower = source.lower()

    # 1. Check for case-specific YAML config
    if case_path:
        config_path = case_path / "mappers" / f"{source_lower}.yaml"
        if config_path.exists():
            mapper = load_config_mapper(config_path)
            if mapper:
                return mapper, "yaml_case"

    # 2. Check for global bundled YAML config
    global_config = CONFIGS_DIR / f"{source_lower}.yaml"
    if global_config.exists():
        mapper = load_config_mapper(global_config)
        if mapper:
            return mapper, "yaml_builtin"

    # 3. Fall back to built-in Python mappers
    if source_lower in BUILTIN_MAPPERS:
        return BUILTIN_MAPPERS[source_lower](), "builtin"

    # 4. Generic mapper (last resort)
    return GenericMapper(), "generic"


def get_mapper_simple(source: str) -> FieldMapper:
    """Get mapper without type info (for backward compatibility)."""
    mapper, _ = get_mapper(source)
    return mapper


__all__ = [
    "FieldMapper",
    "apply_mapper",
    "get_mapper",
    "get_mapper_simple",
    "ConfigMapper",
    "SplunkMapper",
    "KustoMapper",
    "CloudTrailMapper",
    "OktaMapper",
    "GenericMapper",
]
