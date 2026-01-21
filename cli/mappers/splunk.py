"""Splunk field mapper."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from cli.mappers.base import FieldMapper


class SplunkMapper(FieldMapper):
    """Maps Splunk native fields to unified schema."""

    @property
    def field_map(self) -> Dict[str, str]:
        return {
            # Timestamp
            "_time": "event_ts",
            # Source identification
            "sourcetype": "event_type",
            "source": "source_name",
            "index": "source_name",
            # Host/network
            "host": "host",
            "src": "src_ip",
            "src_ip": "src_ip",
            "dest": "dest_ip",
            "dest_ip": "dest_ip",
            "src_port": "src_port",
            "dest_port": "dest_port",
            # User
            "user": "user",
            "src_user": "user",
            "Account_Name": "user",
            # Process
            "process": "process_name",
            "process_name": "process_name",
            "process_id": "process_id",
            "parent_process": "parent_process_name",
            "parent_process_id": "parent_pid",
            "cmdline": "process_cmdline",
            "CommandLine": "process_cmdline",
            # File
            "file_hash": "file_hash",
            "file_path": "file_path",
            "file_name": "file_name",
            # Network
            "url": "url",
            "http_method": "http_method",
            "status": "http_status",
            "bytes_in": "bytes_in",
            "bytes_out": "bytes_out",
            "protocol": "protocol",
            "query": "dns_query",
            # Authentication
            "action": "outcome",
            "result": "outcome",
            "signature": "event_type",
            "EventCode": "event_id",
            "LogonType": "logon_type",
            # Severity
            "severity": "severity",
            "priority": "severity",
            # Message
            "_raw": "message",
            "message": "message",
        }

    def transform_value(self, unified_field: str, value: Any) -> Any:
        if unified_field == "event_ts" and value:
            # Splunk _time can be epoch or ISO string
            try:
                if isinstance(value, (int, float)):
                    dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
                    return dt.isoformat().replace("+00:00", "Z")
                elif isinstance(value, str) and value.replace(".", "").isdigit():
                    dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
                    return dt.isoformat().replace("+00:00", "Z")
            except (ValueError, OSError):
                pass
        return value

    def post_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # Set source_system if not present
        if not row.get("source_system"):
            row["source_system"] = "splunk"
        return row
