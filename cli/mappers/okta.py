"""Okta System Log field mapper."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from cli.mappers.base import FieldMapper


class OktaMapper(FieldMapper):
    """Maps Okta System Log fields to unified schema."""

    @property
    def field_map(self) -> Dict[str, str]:
        return {
            # Timestamp
            "published": "event_ts",
            # Event identification
            "eventType": "event_type",
            "displayMessage": "message",
            "uuid": "event_id",
            # Outcome - handled in post_process for nested structure
            "outcome.result": "outcome",
            "outcome.reason": "message",
            # Severity
            "severity": "severity",
            # Session
            "authenticationContext.externalSessionId": "session_id",
            "transaction.id": "session_id",
        }

    def pre_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract nested actor, client, and target fields."""
        # Extract actor (user who performed action)
        actor = row.get("actor")
        if isinstance(actor, str):
            try:
                actor = json.loads(actor)
            except json.JSONDecodeError:
                actor = None

        if isinstance(actor, dict):
            row["_extracted_user"] = (
                actor.get("alternateId")
                or actor.get("displayName")
                or actor.get("id")
            )

        # Extract client info (source IP, user agent)
        client = row.get("client")
        if isinstance(client, str):
            try:
                client = json.loads(client)
            except json.JSONDecodeError:
                client = None

        if isinstance(client, dict):
            if client.get("ipAddress"):
                row["_extracted_src_ip"] = client["ipAddress"]
            if client.get("userAgent", {}).get("rawUserAgent"):
                row["_extracted_user_agent"] = client["userAgent"]["rawUserAgent"]
            # Geolocation
            geo = client.get("geographicalContext", {})
            if geo.get("city") or geo.get("country"):
                row["_extracted_geo"] = f"{geo.get('city', '')}, {geo.get('country', '')}"

        # Extract outcome
        outcome = row.get("outcome")
        if isinstance(outcome, str):
            try:
                outcome = json.loads(outcome)
            except json.JSONDecodeError:
                outcome = None

        if isinstance(outcome, dict):
            row["_extracted_outcome"] = outcome.get("result", "").lower()
            if outcome.get("reason"):
                row["_extracted_outcome_reason"] = outcome["reason"]

        # Extract target (affected resources/users)
        target = row.get("target")
        if isinstance(target, str):
            try:
                target = json.loads(target)
            except json.JSONDecodeError:
                target = None

        if isinstance(target, list) and target:
            # First target is usually the primary affected entity
            first_target = target[0] if isinstance(target[0], dict) else {}
            target_type = first_target.get("type", "").lower()
            target_id = first_target.get("alternateId") or first_target.get("displayName")
            if target_type == "user" and target_id:
                row["_extracted_target_user"] = target_id
            elif target_id:
                row["_extracted_target"] = f"{target_type}:{target_id}"

        return row

    def post_process(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # Apply extracted fields
        if row.get("_extracted_user") and not row.get("user"):
            row["user"] = row.pop("_extracted_user")
        else:
            row.pop("_extracted_user", None)

        if row.get("_extracted_src_ip") and not row.get("src_ip"):
            row["src_ip"] = row.pop("_extracted_src_ip")
        else:
            row.pop("_extracted_src_ip", None)

        if row.get("_extracted_outcome") and not row.get("outcome"):
            row["outcome"] = row.pop("_extracted_outcome")
        else:
            row.pop("_extracted_outcome", None)

        # Append outcome reason to message
        if row.get("_extracted_outcome_reason"):
            existing_msg = row.get("message", "")
            row["message"] = f"{existing_msg} - {row.pop('_extracted_outcome_reason')}".strip(" -")
        row.pop("_extracted_outcome_reason", None)

        # Use target user as secondary user info
        row.pop("_extracted_target_user", None)
        row.pop("_extracted_target", None)
        row.pop("_extracted_user_agent", None)
        row.pop("_extracted_geo", None)

        if not row.get("source_system"):
            row["source_system"] = "okta"

        return row
