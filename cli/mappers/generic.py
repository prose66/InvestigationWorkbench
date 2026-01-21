"""Generic field mapper with common field name variations."""
from __future__ import annotations

from typing import Any, Dict

from cli.mappers.base import FieldMapper


class GenericMapper(FieldMapper):
    """Fallback mapper that handles common field name variations.
    
    Used when no source-specific mapper is available. Maps common
    variations of field names to the unified schema.
    """

    @property
    def field_map(self) -> Dict[str, str]:
        return {
            # Timestamp variations
            "timestamp": "event_ts",
            "time": "event_ts",
            "datetime": "event_ts",
            "date_time": "event_ts",
            "created_at": "event_ts",
            "occurred_at": "event_ts",
            "@timestamp": "event_ts",
            # Event type variations
            "type": "event_type",
            "action": "event_type",
            "category": "event_type",
            "event_name": "event_type",
            "eventname": "event_type",
            "activity": "event_type",
            # Host variations
            "hostname": "host",
            "host_name": "host",
            "computer": "host",
            "machine": "host",
            "device": "host",
            "server": "host",
            "device_name": "host",
            # User variations
            "username": "user",
            "user_name": "user",
            "account": "user",
            "account_name": "user",
            "principal": "user",
            "actor": "user",
            # Source IP variations
            "source_ip": "src_ip",
            "sourceip": "src_ip",
            "client_ip": "src_ip",
            "clientip": "src_ip",
            "remote_ip": "src_ip",
            "remoteip": "src_ip",
            "ip_address": "src_ip",
            "ipaddress": "src_ip",
            # Dest IP variations
            "destination_ip": "dest_ip",
            "destinationip": "dest_ip",
            "target_ip": "dest_ip",
            "targetip": "dest_ip",
            # Process variations
            "process": "process_name",
            "program": "process_name",
            "application": "process_name",
            "app": "process_name",
            "executable": "process_name",
            "image": "process_name",
            "command": "process_cmdline",
            "commandline": "process_cmdline",
            "command_line": "process_cmdline",
            "cmd": "process_cmdline",
            "pid": "process_id",
            "ppid": "parent_pid",
            # File variations
            "hash": "file_hash",
            "sha256": "file_hash",
            "sha1": "file_hash",
            "md5": "file_hash",
            "path": "file_path",
            "filepath": "file_path",
            "file": "file_name",
            "filename": "file_name",
            # Network
            "port": "dest_port",
            "destination_port": "dest_port",
            "source_port": "src_port",
            "proto": "protocol",
            # URL/DNS
            "domain": "dns_query",
            "query": "dns_query",
            "uri": "url",
            "request_url": "url",
            # Outcome variations
            "result": "outcome",
            "status": "outcome",
            "success": "outcome",
            "disposition": "outcome",
            # Severity variations
            "level": "severity",
            "priority": "severity",
            "risk": "severity",
            "threat_level": "severity",
            # Message variations
            "msg": "message",
            "description": "message",
            "details": "message",
            "summary": "message",
            "raw": "message",
            "log": "message",
        }

    def post_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # Try to infer source_system from available fields
        if not row.get("source_system"):
            if row.get("source"):
                row["source_system"] = row["source"]
        return row
