"""Kusto (Azure Log Analytics / Sentinel) field mapper."""
from __future__ import annotations

from typing import Any, Dict

from cli.mappers.base import FieldMapper


class KustoMapper(FieldMapper):
    """Maps Kusto/Azure Sentinel fields to unified schema."""

    @property
    def field_map(self) -> Dict[str, str]:
        return {
            # Timestamp
            "TimeGenerated": "event_ts",
            "Timestamp": "event_ts",
            "CreatedDateTime": "event_ts",
            # Source
            "Type": "event_type",
            "Category": "event_type",
            "OperationName": "event_type",
            "SourceSystem": "source_name",
            # Host
            "Computer": "host",
            "DeviceName": "host",
            "HostName": "host",
            "_ResourceId": "host",
            # Network
            "SourceIP": "src_ip",
            "SrcIpAddr": "src_ip",
            "ClientIP": "src_ip",
            "CallerIpAddress": "src_ip",
            "DestinationIP": "dest_ip",
            "DstIpAddr": "dest_ip",
            "DestinationPort": "dest_port",
            "SourcePort": "src_port",
            # User
            "Account": "user",
            "UserPrincipalName": "user",
            "AccountName": "user",
            "TargetUserName": "user",
            "InitiatingUser": "user",
            "UserId": "user_sid",
            # Process
            "ProcessName": "process_name",
            "FileName": "process_name",
            "Process": "process_name",
            "ProcessId": "process_id",
            "ProcessCommandLine": "process_cmdline",
            "CommandLine": "process_cmdline",
            "ParentProcessName": "parent_process_name",
            "InitiatingProcessFileName": "parent_process_name",
            "ParentProcessId": "parent_pid",
            # File
            "SHA256": "file_hash",
            "FileHash": "file_hash",
            "MD5": "file_hash",
            "FilePath": "file_path",
            "FolderPath": "file_path",
            # Registry
            "RegistryKey": "registry_key",
            "RegistryValueName": "registry_value_name",
            "RegistryValueData": "registry_value_data",
            # URL/DNS
            "Url": "url",
            "RequestUri": "url",
            "RemoteUrl": "url",
            "DnsQuery": "dns_query",
            "QueryName": "dns_query",
            # Auth
            "ResultType": "outcome",
            "Result": "outcome",
            "Status": "outcome",
            "ResultDescription": "message",
            "LogonType": "logon_type",
            "AuthenticationMethod": "logon_type",
            # Severity
            "Severity": "severity",
            "AlertSeverity": "severity",
            "Level": "severity",
            # MITRE
            "Tactics": "tactic",
            "Techniques": "technique",
            # Misc
            "ActivityId": "event_id",
            "CorrelationId": "session_id",
            "Message": "message",
            "Description": "message",
        }

    def post_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        if not row.get("source_system"):
            row["source_system"] = "kusto"
        return row
