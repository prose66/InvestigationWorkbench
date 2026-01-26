"""File ingestion API endpoints."""
from __future__ import annotations

import base64
import csv
import io
import json
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from fastapi import APIRouter, HTTPException

from api.services.db import list_cases
from api.schemas.ingest import (
    PreviewRequest,
    PreviewResponse,
    IngestRequest,
    IngestResponse,
    MapperInfo,
    FieldMapping,
    BatchPreviewRequest,
    BatchPreviewResponse,
    BatchIngestRequest,
    BatchIngestResponse,
)
from cli.commands import case_paths, add_run, ingest_run, init_case
from cli.mappers import get_mapper, BUILTIN_MAPPERS, CONFIGS_DIR
from cli.mappers.config_mapper import load_config_mapper
from cli.ingest import REQUIRED_FIELDS, EXTENDED_FIELDS

router = APIRouter(prefix="/cases/{case_id}/ingest", tags=["ingest"])


# Common field patterns for auto-suggestion
FIELD_PATTERNS: Dict[str, List[str]] = {
    "event_ts": ["timestamp", "time", "datetime", "_time", "eventtime", "created_at", "date", "ts", "when", "occurred"],
    "event_type": ["type", "action", "category", "eventname", "activity", "event_name", "operation", "name"],
    "host": ["hostname", "host_name", "computer", "machine", "device", "devicename", "host", "computername"],
    "user": ["username", "user_name", "account", "actor", "principal", "userid", "user_id", "accountname", "user"],
    "src_ip": ["source_ip", "sourceip", "src", "client_ip", "remote_ip", "srcip", "source_address", "src_addr"],
    "dest_ip": ["destination_ip", "destip", "dst", "target_ip", "dest", "dstip", "destination_address", "dst_addr"],
    "src_port": ["source_port", "srcport", "sport", "src_port"],
    "dest_port": ["destination_port", "dstport", "dport", "dest_port"],
    "process_name": ["process", "process_name", "image", "imagepath", "executable", "exe", "program"],
    "process_cmdline": ["command_line", "commandline", "cmdline", "cmd", "command"],
    "file_path": ["filepath", "file_path", "path", "filename", "file_name", "object_name"],
    "file_hash": ["hash", "md5", "sha256", "sha1", "filehash", "file_hash"],
    "outcome": ["outcome", "result", "status", "success", "verdict"],
    "severity": ["severity", "level", "priority", "risk"],
    "message": ["message", "msg", "description", "details", "summary", "raw"],
    "url": ["url", "uri", "link", "web_address"],
    "dns_query": ["query", "dns_query", "domain", "fqdn"],
    "protocol": ["protocol", "proto", "app_protocol"],
}


def suggest_mapping(source_field: str) -> Optional[str]:
    """Suggest a unified field mapping for a source field."""
    normalized = source_field.lower().replace("-", "_").replace(" ", "_")

    for unified, patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            # Exact match
            if normalized == pattern:
                return unified
            # Contains pattern
            if pattern in normalized or normalized in pattern:
                return unified

    return None


def parse_file_content(content: str, filename: str) -> Tuple[List[Dict[str, Any]], str, int]:
    """Parse base64-encoded file content.

    Returns:
        Tuple of (rows, format, total_count)
    """
    try:
        decoded = base64.b64decode(content).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode file content: {e}")

    rows: List[Dict[str, Any]] = []
    file_format = "ndjson"

    if filename.lower().endswith(".csv"):
        file_format = "csv"
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)
    else:
        # Try NDJSON
        for line in decoded.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # Fall back to CSV if JSON parsing fails
                file_format = "csv"
                reader = csv.DictReader(io.StringIO(decoded))
                rows = list(reader)
                break

    return rows, file_format, len(rows)


@router.post("/preview", response_model=PreviewResponse)
def upload_preview(case_id: str, request: PreviewRequest):
    """Upload file and return preview data with suggested mappings."""
    # Parse file content
    rows, file_format, total_rows = parse_file_content(request.content, request.filename)

    if not rows:
        raise HTTPException(status_code=400, detail="No data found in file")

    # Get source fields from first row
    source_fields = list(rows[0].keys()) if rows else []

    # Get mapper for this source
    paths = case_paths(case_id)
    case_dir = paths["case_dir"] if paths["case_dir"].exists() else None
    mapper, mapper_type = get_mapper(request.source, case_dir)

    # Build suggested mappings
    # First, use mapper's field_map if available
    suggested_mappings: Dict[str, str] = {}

    # Add mappings from the existing mapper
    for source_field in source_fields:
        # Check if mapper has this field
        if source_field in mapper.field_map:
            suggested_mappings[source_field] = mapper.field_map[source_field]
        elif source_field.lower() in {k.lower() for k in mapper.field_map}:
            # Case-insensitive match
            for k, v in mapper.field_map.items():
                if k.lower() == source_field.lower():
                    suggested_mappings[source_field] = v
                    break
        else:
            # Fall back to pattern matching
            suggestion = suggest_mapping(source_field)
            if suggestion:
                suggested_mappings[source_field] = suggestion

    # Return preview (first 50 rows)
    preview_rows = rows[:50]

    return PreviewResponse(
        source_fields=source_fields,
        preview_rows=preview_rows,
        total_rows=total_rows,
        suggested_mappings=suggested_mappings,
        file_format=file_format,
        mapper_type=mapper_type,
    )


@router.post("/commit", response_model=IngestResponse)
def commit_ingest(case_id: str, request: IngestRequest):
    """Commit the ingestion with user-defined field mappings."""
    # Ensure case exists
    cases = list_cases()
    if case_id not in cases:
        # Initialize the case
        try:
            init_case(case_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize case: {e}")

    paths = case_paths(case_id)

    # Parse file content
    rows, file_format, _ = parse_file_content(request.content, request.filename)

    if not rows:
        raise HTTPException(status_code=400, detail="No data found in file")

    # Build custom field map from request
    custom_field_map: Dict[str, str] = {}
    for mapping in request.field_mappings:
        if mapping.unified_field:  # Skip ignored fields
            custom_field_map[mapping.source_field] = mapping.unified_field

    # Save YAML mapper if requested
    mapper_saved = False
    if request.save_mapper and custom_field_map:
        mapper_saved = save_yaml_mapper(
            case_id,
            request.source,
            custom_field_map,
            paths["case_dir"],
        )

    # Write content to temp file
    suffix = ".csv" if file_format == "csv" else ".ndjson"
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as f:
        decoded = base64.b64decode(request.content).decode("utf-8")
        f.write(decoded)
        temp_path = Path(f.name)

    try:
        # Add run
        run_id = add_run(
            case_id=case_id,
            source=request.source,
            query_name=request.query_name,
            query_text=None,
            time_start=request.time_start,
            time_end=request.time_end,
            file_path=temp_path,
            allow_duplicate=True,  # Allow re-upload for now
        )

        # Ingest the run
        result = ingest_run(
            case_id=case_id,
            run_id=run_id,
            skip_errors=True,
            lenient=True,
        )

        return IngestResponse(
            run_id=run_id,
            events_ingested=result.events_ingested,
            events_skipped=result.events_skipped,
            errors=result.errors[:10],  # Limit errors in response
            suggestions=result.suggestions,
            mapper_saved=mapper_saved,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
    finally:
        # Clean up temp file
        try:
            temp_path.unlink()
        except Exception:
            pass


@router.get("/mappers", response_model=List[MapperInfo])
def list_mappers(case_id: str):
    """List available mappers for auto-suggestion."""
    mappers: List[MapperInfo] = []

    # Case-specific YAML mappers
    paths = case_paths(case_id)
    case_mappers_dir = paths["case_dir"] / "mappers"
    if case_mappers_dir.exists():
        for yaml_file in case_mappers_dir.glob("*.yaml"):
            config_mapper = load_config_mapper(yaml_file)
            if config_mapper:
                mappers.append(MapperInfo(
                    name=yaml_file.stem,
                    type="yaml_case",
                    description=config_mapper.description,
                    source=config_mapper.source_name,
                    field_count=len(config_mapper.field_map),
                ))

    # Global YAML mappers
    if CONFIGS_DIR.exists():
        for yaml_file in CONFIGS_DIR.glob("*.yaml"):
            config_mapper = load_config_mapper(yaml_file)
            if config_mapper:
                mappers.append(MapperInfo(
                    name=yaml_file.stem,
                    type="yaml_builtin",
                    description=config_mapper.description,
                    source=config_mapper.source_name,
                    field_count=len(config_mapper.field_map),
                ))

    # Built-in Python mappers
    for source, mapper_class in BUILTIN_MAPPERS.items():
        instance = mapper_class()
        mappers.append(MapperInfo(
            name=source,
            type="builtin",
            description=f"Built-in {source.title()} mapper",
            source=source,
            field_count=len(instance.field_map),
        ))

    return mappers


@router.get("/unified-fields")
def get_unified_fields():
    """Get list of unified schema fields for mapping UI."""
    required = [{"name": f, "required": True} for f in REQUIRED_FIELDS]
    extended = [{"name": f, "required": False} for f in EXTENDED_FIELDS]
    return {"fields": required + extended}


def save_yaml_mapper(
    case_id: str,
    source: str,
    field_map: Dict[str, str],
    case_dir: Path,
) -> bool:
    """Save a YAML mapper config for a case."""
    try:
        mappers_dir = case_dir / "mappers"
        mappers_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "source": source,
            "description": f"Custom mapper for {source} created via UI",
            "field_map": field_map,
            "required_only": ["event_ts", "event_type"],
        }

        mapper_path = mappers_dir / f"{source.lower()}.yaml"
        with mapper_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, default_flow_style=False)

        return True
    except Exception:
        return False


@router.post("/preview-batch", response_model=BatchPreviewResponse)
def preview_batch(case_id: str, request: BatchPreviewRequest):
    """Preview multiple files and return merged schema."""
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")

    file_previews: List[PreviewResponse] = []
    all_fields: Dict[str, List[int]] = {}  # field -> file indices
    all_mappings: Dict[str, str] = {}

    for idx, file_info in enumerate(request.files):
        # Parse file content
        rows, file_format, total_rows = parse_file_content(
            file_info.content, file_info.filename
        )

        if not rows:
            raise HTTPException(
                status_code=400,
                detail=f"No data found in file: {file_info.filename}"
            )

        # Get source fields from first row
        source_fields = list(rows[0].keys()) if rows else []

        # Track which files have each field
        for field in source_fields:
            if field not in all_fields:
                all_fields[field] = []
            all_fields[field].append(idx)

        # Get mapper for this source
        paths = case_paths(case_id)
        case_dir = paths["case_dir"] if paths["case_dir"].exists() else None
        mapper, mapper_type = get_mapper(file_info.source, case_dir)

        # Build suggested mappings for this file
        suggested_mappings: Dict[str, str] = {}
        for source_field in source_fields:
            if source_field in mapper.field_map:
                suggested_mappings[source_field] = mapper.field_map[source_field]
            elif source_field.lower() in {k.lower() for k in mapper.field_map}:
                for k, v in mapper.field_map.items():
                    if k.lower() == source_field.lower():
                        suggested_mappings[source_field] = v
                        break
            else:
                suggestion = suggest_mapping(source_field)
                if suggestion:
                    suggested_mappings[source_field] = suggestion

        # Collect mappings (first file's mapping wins for each field)
        for field, unified in suggested_mappings.items():
            if field not in all_mappings:
                all_mappings[field] = unified

        preview_rows = rows[:50]

        file_previews.append(PreviewResponse(
            source_fields=source_fields,
            preview_rows=preview_rows,
            total_rows=total_rows,
            suggested_mappings=suggested_mappings,
            file_format=file_format,
            mapper_type=mapper_type,
        ))

    # Build merged schema (sorted unique fields)
    merged_fields = sorted(all_fields.keys())

    return BatchPreviewResponse(
        file_previews=file_previews,
        merged_fields=merged_fields,
        field_sources=all_fields,
        suggested_mappings=all_mappings,
    )


@router.post("/commit-batch", response_model=BatchIngestResponse)
def commit_batch(case_id: str, request: BatchIngestRequest):
    """Commit multiple files with shared mappings."""
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Ensure case exists
    cases = list_cases()
    if case_id not in cases:
        try:
            init_case(case_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize case: {e}")

    paths = case_paths(case_id)

    # Build custom field map from request
    custom_field_map: Dict[str, str] = {}
    for mapping in request.field_mappings:
        if mapping.unified_field:
            custom_field_map[mapping.source_field] = mapping.unified_field

    # Save mapper if requested (use first file's source)
    mapper_saved = False
    if request.save_mapper and custom_field_map and request.files:
        # Save a combined mapper for each unique source
        unique_sources = set(f.source for f in request.files)
        for source in unique_sources:
            saved = save_yaml_mapper(
                case_id,
                source,
                custom_field_map,
                paths["case_dir"],
            )
            if saved:
                mapper_saved = True

    results: List[IngestResponse] = []
    total_ingested = 0
    total_skipped = 0

    for file_info in request.files:
        # Parse file content
        rows, file_format, _ = parse_file_content(file_info.content, file_info.filename)

        if not rows:
            results.append(IngestResponse(
                run_id="",
                events_ingested=0,
                events_skipped=0,
                errors=[{"error": f"No data found in file: {file_info.filename}"}],
                suggestions=[],
                mapper_saved=False,
            ))
            continue

        # Write content to temp file
        suffix = ".csv" if file_format == "csv" else ".ndjson"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as f:
            decoded = base64.b64decode(file_info.content).decode("utf-8")
            f.write(decoded)
            temp_path = Path(f.name)

        try:
            # Add run
            run_id = add_run(
                case_id=case_id,
                source=file_info.source,
                query_name=file_info.query_name,
                query_text=None,
                time_start=request.time_start,
                time_end=request.time_end,
                file_path=temp_path,
                allow_duplicate=True,
            )

            # Ingest the run
            result = ingest_run(
                case_id=case_id,
                run_id=run_id,
                skip_errors=True,
                lenient=True,
            )

            response = IngestResponse(
                run_id=run_id,
                events_ingested=result.events_ingested,
                events_skipped=result.events_skipped,
                errors=result.errors[:10],
                suggestions=result.suggestions,
                mapper_saved=mapper_saved,
            )
            results.append(response)
            total_ingested += result.events_ingested
            total_skipped += result.events_skipped

        except Exception as e:
            results.append(IngestResponse(
                run_id="",
                events_ingested=0,
                events_skipped=0,
                errors=[{"error": str(e)}],
                suggestions=[],
                mapper_saved=False,
            ))
        finally:
            try:
                temp_path.unlink()
            except Exception:
                pass

    return BatchIngestResponse(
        results=results,
        total_ingested=total_ingested,
        total_skipped=total_skipped,
    )
