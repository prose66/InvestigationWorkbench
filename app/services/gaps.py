"""Timeline gap detection service."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import pandas as pd

from services.db import query_df, time_bounds


@dataclass
class TimeGap:
    """Represents a gap in event coverage."""
    start: datetime
    end: datetime
    duration: timedelta
    expected_events: int  # Based on surrounding activity
    severity: str  # "low", "medium", "high"
    affected_sources: List[str]


def detect_timeline_gaps(
    case_id: str,
    bucket_minutes: int = 60,
    min_gap_buckets: int = 2,
    source_filter: Optional[str] = None,
) -> Tuple[pd.DataFrame, List[TimeGap]]:
    """Detect gaps in event timeline.
    
    Args:
        case_id: Case identifier
        bucket_minutes: Size of time buckets in minutes
        min_gap_buckets: Minimum consecutive empty buckets to be considered a gap
        source_filter: Optional filter for specific source system
        
    Returns:
        Tuple of (bucket_df with event counts, list of detected gaps)
    """
    min_ts, max_ts = time_bounds(case_id)
    if not min_ts or not max_ts:
        return pd.DataFrame(), []
    
    # Build bucket query
    bucket_fmt = "%Y-%m-%d %H:%M:00"
    if bucket_minutes >= 60:
        bucket_fmt = "%Y-%m-%d %H:00:00"
    if bucket_minutes >= 1440:  # Daily
        bucket_fmt = "%Y-%m-%d"
    
    where_clause = "case_id = ?"
    params: List = [case_id]
    
    if source_filter:
        where_clause += " AND source_system = ?"
        params.append(source_filter)
    
    # Query event counts per bucket
    bucket_df = query_df(
        case_id,
        f"""
        SELECT 
            strftime('{bucket_fmt}', event_ts) AS bucket,
            COUNT(*) AS count,
            COUNT(DISTINCT source_system) AS source_count
        FROM events
        WHERE {where_clause}
        GROUP BY bucket
        ORDER BY bucket
        """,
        tuple(params),
    )
    
    if bucket_df.empty:
        return bucket_df, []
    
    # Generate complete time range
    bucket_df["bucket_ts"] = pd.to_datetime(bucket_df["bucket"], utc=True)
    
    # Create full time range
    start = bucket_df["bucket_ts"].min()
    end = bucket_df["bucket_ts"].max()
    
    freq = f"{bucket_minutes}min" if bucket_minutes < 1440 else "D"
    full_range = pd.date_range(start=start, end=end, freq=freq, tz=timezone.utc)
    
    full_df = pd.DataFrame({"bucket_ts": full_range})
    merged = full_df.merge(bucket_df, on="bucket_ts", how="left")
    merged["count"] = merged["count"].fillna(0).astype(int)
    merged["source_count"] = merged["source_count"].fillna(0).astype(int)
    merged["is_gap"] = merged["count"] == 0
    
    # Detect consecutive gaps
    gaps: List[TimeGap] = []
    gap_start: Optional[datetime] = None
    gap_buckets = 0
    
    # Calculate average events per bucket for severity
    avg_events = merged[merged["count"] > 0]["count"].mean() if (merged["count"] > 0).any() else 0
    
    for idx, row in merged.iterrows():
        if row["is_gap"]:
            if gap_start is None:
                gap_start = row["bucket_ts"]
            gap_buckets += 1
        else:
            if gap_start is not None and gap_buckets >= min_gap_buckets:
                gap_end = row["bucket_ts"]
                duration = gap_end - gap_start
                
                # Determine severity based on duration and expected activity
                expected = int(avg_events * gap_buckets)
                if duration > timedelta(hours=24):
                    severity = "high"
                elif duration > timedelta(hours=4):
                    severity = "medium"
                else:
                    severity = "low"
                
                # Get sources that were active before the gap
                affected_sources = get_active_sources_before_gap(case_id, gap_start)
                
                gaps.append(TimeGap(
                    start=gap_start,
                    end=gap_end,
                    duration=duration,
                    expected_events=expected,
                    severity=severity,
                    affected_sources=affected_sources,
                ))
            
            gap_start = None
            gap_buckets = 0
    
    # Handle gap at end of timeline
    if gap_start is not None and gap_buckets >= min_gap_buckets:
        gap_end = merged["bucket_ts"].iloc[-1] + timedelta(minutes=bucket_minutes)
        duration = gap_end - gap_start
        expected = int(avg_events * gap_buckets)
        severity = "high" if duration > timedelta(hours=24) else "medium" if duration > timedelta(hours=4) else "low"
        affected_sources = get_active_sources_before_gap(case_id, gap_start)
        
        gaps.append(TimeGap(
            start=gap_start,
            end=gap_end,
            duration=duration,
            expected_events=expected,
            severity=severity,
            affected_sources=affected_sources,
        ))
    
    return merged, gaps


def get_active_sources_before_gap(case_id: str, gap_start: datetime, lookback_hours: int = 4) -> List[str]:
    """Get sources that were active before a gap."""
    lookback_start = gap_start - timedelta(hours=lookback_hours)
    
    df = query_df(
        case_id,
        """
        SELECT DISTINCT source_system
        FROM events
        WHERE case_id = ?
          AND event_ts >= ?
          AND event_ts < ?
        """,
        (case_id, lookback_start.isoformat(), gap_start.isoformat()),
    )
    
    return df["source_system"].tolist() if not df.empty else []


def get_source_coverage(case_id: str) -> pd.DataFrame:
    """Get time coverage for each source system."""
    df = query_df(
        case_id,
        """
        SELECT 
            source_system,
            MIN(event_ts) AS first_event,
            MAX(event_ts) AS last_event,
            COUNT(*) AS event_count,
            COUNT(DISTINCT strftime('%Y-%m-%d %H:00:00', event_ts)) AS active_hours
        FROM events
        WHERE case_id = ?
        GROUP BY source_system
        ORDER BY first_event
        """,
        (case_id,),
    )
    
    if df.empty:
        return df
    
    # Calculate coverage percentage
    df["first_ts"] = pd.to_datetime(df["first_event"], utc=True)
    df["last_ts"] = pd.to_datetime(df["last_event"], utc=True)
    
    total_start = df["first_ts"].min()
    total_end = df["last_ts"].max()
    total_hours = max(1, (total_end - total_start).total_seconds() / 3600)
    
    df["coverage_pct"] = (df["active_hours"] / total_hours * 100).round(1)
    
    return df[["source_system", "first_event", "last_event", "event_count", "active_hours", "coverage_pct"]]
