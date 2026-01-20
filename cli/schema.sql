PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY,
  title TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS query_runs (
  run_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  source_system TEXT NOT NULL,
  query_name TEXT NOT NULL,
  query_text TEXT,
  executed_at TEXT,
  time_start TEXT,
  time_end TEXT,
  raw_path TEXT NOT NULL,
  row_count INTEGER,
  file_hash TEXT,
  ingested_at TEXT,
  FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS events (
  event_pk INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  event_ts TEXT NOT NULL,
  source_system TEXT NOT NULL,
  source_name TEXT,
  event_type TEXT NOT NULL,
  host TEXT,
  user TEXT,
  src_ip TEXT,
  dest_ip TEXT,
  process_name TEXT,
  process_cmdline TEXT,
  process_id TEXT,
  parent_pid TEXT,
  parent_process_name TEXT,
  parent_process_cmdline TEXT,
  file_hash TEXT,
  file_path TEXT,
  file_name TEXT,
  file_extension TEXT,
  file_size TEXT,
  file_owner TEXT,
  registry_hive TEXT,
  registry_key TEXT,
  registry_value TEXT,
  registry_value_name TEXT,
  registry_value_type TEXT,
  registry_value_data TEXT,
  dns_query TEXT,
  url TEXT,
  http_method TEXT,
  http_status TEXT,
  bytes_in TEXT,
  bytes_out TEXT,
  src_port TEXT,
  dest_port TEXT,
  protocol TEXT,
  event_id TEXT,
  logon_type TEXT,
  session_id TEXT,
  user_sid TEXT,
  integrity_level TEXT,
  artifact_type TEXT,
  artifact_path TEXT,
  edr_alert_id TEXT,
  tactic TEXT,
  technique TEXT,
  outcome TEXT,
  severity TEXT,
  message TEXT,
  source_event_id TEXT,
  raw_ref TEXT,
  raw_json TEXT,
  extras_json TEXT,
  fingerprint TEXT,
  FOREIGN KEY (case_id) REFERENCES cases(case_id),
  FOREIGN KEY (run_id) REFERENCES query_runs(run_id)
);

CREATE TABLE IF NOT EXISTS entities (
  entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_value TEXT NOT NULL,
  first_seen TEXT,
  last_seen TEXT,
  notes TEXT,
  tags TEXT,
  FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS event_entities (
  event_pk INTEGER NOT NULL,
  entity_id INTEGER NOT NULL,
  PRIMARY KEY (event_pk, entity_id),
  FOREIGN KEY (event_pk) REFERENCES events(event_pk),
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE IF NOT EXISTS event_fields (
  event_pk INTEGER NOT NULL,
  case_id TEXT NOT NULL,
  field_name TEXT NOT NULL,
  field_value TEXT,
  PRIMARY KEY (event_pk, field_name),
  FOREIGN KEY (event_pk) REFERENCES events(event_pk),
  FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE INDEX IF NOT EXISTS idx_events_case_ts ON events(case_id, event_ts);
CREATE INDEX IF NOT EXISTS idx_events_case_host ON events(case_id, host);
CREATE INDEX IF NOT EXISTS idx_events_case_user ON events(case_id, user);
CREATE INDEX IF NOT EXISTS idx_events_case_src_ip ON events(case_id, src_ip);
CREATE INDEX IF NOT EXISTS idx_events_case_dest_ip ON events(case_id, dest_ip);
CREATE INDEX IF NOT EXISTS idx_events_case_event_type ON events(case_id, event_type);
CREATE INDEX IF NOT EXISTS idx_events_case_source_system ON events(case_id, source_system);
CREATE INDEX IF NOT EXISTS idx_events_case_source_event_id ON events(case_id, source_event_id);
CREATE INDEX IF NOT EXISTS idx_event_fields_case_name ON event_fields(case_id, field_name);

CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique_source_event
  ON events(case_id, source_system, source_event_id)
  WHERE source_event_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique_fingerprint
  ON events(case_id, fingerprint)
  WHERE fingerprint IS NOT NULL;
