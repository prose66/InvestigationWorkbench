"""Global event search service."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from services.db import query_df


def search_events(
    case_id: str,
    keyword: str,
    limit: int = 100,
) -> pd.DataFrame:
    """Search events by keyword across multiple fields.
    
    Searches: message, event_type, host, user, src_ip, dest_ip, 
              process_name, process_cmdline, file_path, url, dns_query
    
    Args:
        case_id: Case identifier
        keyword: Search keyword (case-insensitive)
        limit: Maximum results to return
        
    Returns:
        DataFrame of matching events
    """
    search_pattern = f"%{keyword}%"
    sql = """
        SELECT
          event_pk, event_ts, source_system, event_type, host, user,
          src_ip, dest_ip, process_name, outcome, severity, message
        FROM events
        WHERE case_id = ?
          AND (
            message LIKE ? COLLATE NOCASE
            OR event_type LIKE ? COLLATE NOCASE
            OR host LIKE ? COLLATE NOCASE
            OR user LIKE ? COLLATE NOCASE
            OR src_ip LIKE ? COLLATE NOCASE
            OR dest_ip LIKE ? COLLATE NOCASE
            OR process_name LIKE ? COLLATE NOCASE
            OR process_cmdline LIKE ? COLLATE NOCASE
            OR file_path LIKE ? COLLATE NOCASE
            OR url LIKE ? COLLATE NOCASE
            OR dns_query LIKE ? COLLATE NOCASE
          )
        ORDER BY event_ts DESC
        LIMIT ?
    """
    params = (case_id,) + (search_pattern,) * 11 + (limit,)
    return query_df(case_id, sql, params)


def count_search_results(case_id: str, keyword: str) -> int:
    """Count total matching events for a keyword search."""
    search_pattern = f"%{keyword}%"
    sql = """
        SELECT COUNT(*) as count
        FROM events
        WHERE case_id = ?
          AND (
            message LIKE ? COLLATE NOCASE
            OR event_type LIKE ? COLLATE NOCASE
            OR host LIKE ? COLLATE NOCASE
            OR user LIKE ? COLLATE NOCASE
            OR src_ip LIKE ? COLLATE NOCASE
            OR dest_ip LIKE ? COLLATE NOCASE
            OR process_name LIKE ? COLLATE NOCASE
            OR process_cmdline LIKE ? COLLATE NOCASE
            OR file_path LIKE ? COLLATE NOCASE
            OR url LIKE ? COLLATE NOCASE
            OR dns_query LIKE ? COLLATE NOCASE
          )
    """
    params = (case_id,) + (search_pattern,) * 11
    df = query_df(case_id, sql, params)
    return int(df["count"].iloc[0]) if not df.empty else 0
