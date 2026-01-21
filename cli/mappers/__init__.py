"""Source-specific field mappers for normalizing SIEM exports to unified schema."""
from __future__ import annotations

from typing import Callable, Dict

from cli.mappers.base import FieldMapper, apply_mapper
from cli.mappers.splunk import SplunkMapper
from cli.mappers.kusto import KustoMapper
from cli.mappers.cloudtrail import CloudTrailMapper
from cli.mappers.okta import OktaMapper
from cli.mappers.generic import GenericMapper

MAPPERS: Dict[str, FieldMapper] = {
    "splunk": SplunkMapper(),
    "kusto": KustoMapper(),
    "cloudtrail": CloudTrailMapper(),
    "aws": CloudTrailMapper(),
    "okta": OktaMapper(),
}


def get_mapper(source: str) -> FieldMapper:
    """Get the appropriate mapper for a source system."""
    return MAPPERS.get(source.lower(), GenericMapper())


__all__ = [
    "FieldMapper",
    "apply_mapper",
    "get_mapper",
    "SplunkMapper",
    "KustoMapper",
    "CloudTrailMapper",
    "OktaMapper",
    "GenericMapper",
]
