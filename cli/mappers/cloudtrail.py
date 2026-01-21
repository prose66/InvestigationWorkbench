"""AWS CloudTrail field mapper."""
from __future__ import annotations

import json
from typing import Any, Dict

from cli.mappers.base import FieldMapper


class CloudTrailMapper(FieldMapper):
    """Maps AWS CloudTrail fields to unified schema."""

    @property
    def field_map(self) -> Dict[str, str]:
        return {
            # Timestamp
            "eventTime": "event_ts",
            # Event identification
            "eventName": "event_type",
            "eventType": "event_type",
            "eventSource": "source_name",
            "eventID": "event_id",
            # Source
            "sourceIPAddress": "src_ip",
            "userAgent": "message",
            # User - handled in post_process for nested userIdentity
            "userName": "user",
            # Region/resource as host
            "awsRegion": "host",
            # Request details
            "requestID": "session_id",
            # Outcome
            "errorCode": "outcome",
            "errorMessage": "message",
        }

    def pre_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract nested userIdentity fields."""
        user_identity = row.get("userIdentity")
        if isinstance(user_identity, str):
            try:
                user_identity = json.loads(user_identity)
            except json.JSONDecodeError:
                user_identity = None

        if isinstance(user_identity, dict):
            # Extract user from various identity types
            user = (
                user_identity.get("userName")
                or user_identity.get("principalId")
                or user_identity.get("arn", "").split("/")[-1]
            )
            if user:
                row["_extracted_user"] = user
            
            # Extract account
            if user_identity.get("accountId"):
                row["_extracted_account"] = user_identity["accountId"]

        # Extract request parameters if present
        request_params = row.get("requestParameters")
        if isinstance(request_params, str):
            try:
                request_params = json.loads(request_params)
            except json.JSONDecodeError:
                request_params = None

        if isinstance(request_params, dict):
            # Common patterns in request parameters
            if request_params.get("instanceId"):
                row["_extracted_host"] = request_params["instanceId"]
            if request_params.get("bucketName"):
                row["_extracted_file_path"] = f"s3://{request_params['bucketName']}"

        return row

    def post_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # Apply extracted fields
        if row.get("_extracted_user") and not row.get("user"):
            row["user"] = row.pop("_extracted_user")
        else:
            row.pop("_extracted_user", None)

        if row.get("_extracted_host") and not row.get("host"):
            row["host"] = row.pop("_extracted_host")
        else:
            row.pop("_extracted_host", None)

        if row.get("_extracted_file_path") and not row.get("file_path"):
            row["file_path"] = row.pop("_extracted_file_path")
        else:
            row.pop("_extracted_file_path", None)

        row.pop("_extracted_account", None)

        # Set outcome based on errorCode presence
        if not row.get("outcome"):
            row["outcome"] = "failure" if row.get("errorCode") else "success"

        if not row.get("source_system"):
            row["source_system"] = "aws"

        return row
