/**
 * Field auto-suggestion logic for mapping source fields to unified schema.
 */

// Common patterns for each unified field
export const FIELD_PATTERNS: Record<string, string[]> = {
  event_ts: [
    "timestamp",
    "time",
    "datetime",
    "_time",
    "eventtime",
    "created_at",
    "date",
    "ts",
    "when",
    "occurred",
    "event_time",
    "log_time",
    "recorded_at",
  ],
  event_type: [
    "type",
    "action",
    "category",
    "eventname",
    "activity",
    "event_name",
    "operation",
    "name",
    "event_id",
    "event_category",
  ],
  host: [
    "hostname",
    "host_name",
    "computer",
    "machine",
    "device",
    "devicename",
    "host",
    "computername",
    "workstation",
    "server",
    "endpoint",
  ],
  user: [
    "username",
    "user_name",
    "account",
    "actor",
    "principal",
    "userid",
    "user_id",
    "accountname",
    "user",
    "login",
    "identity",
  ],
  src_ip: [
    "source_ip",
    "sourceip",
    "src",
    "client_ip",
    "remote_ip",
    "srcip",
    "source_address",
    "src_addr",
    "source",
    "client_address",
  ],
  dest_ip: [
    "destination_ip",
    "destip",
    "dst",
    "target_ip",
    "dest",
    "dstip",
    "destination_address",
    "dst_addr",
    "destination",
    "server_ip",
  ],
  src_port: ["source_port", "srcport", "sport", "src_port", "client_port"],
  dest_port: ["destination_port", "dstport", "dport", "dest_port", "server_port", "port"],
  process_name: [
    "process",
    "process_name",
    "image",
    "imagepath",
    "executable",
    "exe",
    "program",
    "application",
    "process_image",
  ],
  process_cmdline: [
    "command_line",
    "commandline",
    "cmdline",
    "cmd",
    "command",
    "process_commandline",
    "arguments",
  ],
  file_path: [
    "filepath",
    "file_path",
    "path",
    "filename",
    "file_name",
    "object_name",
    "target_path",
  ],
  file_hash: ["hash", "md5", "sha256", "sha1", "filehash", "file_hash", "checksum"],
  outcome: ["outcome", "result", "status", "success", "verdict", "disposition"],
  severity: ["severity", "level", "priority", "risk", "risk_level", "importance"],
  message: [
    "message",
    "msg",
    "description",
    "details",
    "summary",
    "raw",
    "raw_message",
    "log_message",
  ],
  url: ["url", "uri", "link", "web_address", "request_url", "target_url"],
  dns_query: ["query", "dns_query", "domain", "fqdn", "dns_name", "requested_domain"],
  protocol: ["protocol", "proto", "app_protocol", "network_protocol"],
  bytes_in: ["bytes_in", "received_bytes", "rx_bytes", "in_bytes", "download"],
  bytes_out: ["bytes_out", "sent_bytes", "tx_bytes", "out_bytes", "upload"],
  tactic: ["tactic", "mitre_tactic", "attack_tactic"],
  technique: ["technique", "mitre_technique", "attack_technique", "technique_id"],
};

// Required fields that MUST be mapped for successful ingestion
export const REQUIRED_FIELDS = ["event_ts", "event_type"];

// Entity fields that can be extracted for pivoting
export const ENTITY_FIELDS = [
  "host",
  "user",
  "src_ip",
  "dest_ip",
  "file_hash",
  "process_name",
];

/**
 * Suggest a unified field mapping for a source field name.
 */
export function suggestMapping(sourceField: string): string | null {
  const normalized = sourceField
    .toLowerCase()
    .replace(/[-\s]/g, "_")
    .replace(/[^a-z0-9_]/g, "");

  for (const [unified, patterns] of Object.entries(FIELD_PATTERNS)) {
    for (const pattern of patterns) {
      // Exact match
      if (normalized === pattern) {
        return unified;
      }
      // Contains pattern (bidirectional)
      if (normalized.includes(pattern) || pattern.includes(normalized)) {
        return unified;
      }
    }
  }

  return null;
}

/**
 * Get all unified fields available for mapping.
 */
export function getUnifiedFields(): string[] {
  return Object.keys(FIELD_PATTERNS);
}

/**
 * Check if a mapping is valid (has required fields).
 */
export function validateMappings(
  mappings: Record<string, string | null>
): { valid: boolean; missing: string[] } {
  const mappedUnifiedFields = new Set(
    Object.values(mappings).filter((v): v is string => v !== null)
  );

  const missing: string[] = [];
  for (const required of REQUIRED_FIELDS) {
    if (!mappedUnifiedFields.has(required)) {
      missing.push(required);
    }
  }

  return {
    valid: missing.length === 0,
    missing,
  };
}

/**
 * Get suggested entity fields from current mappings.
 */
export function suggestEntityFields(mappings: Record<string, string | null>): string[] {
  const suggested: string[] = [];

  for (const [sourceField, unifiedField] of Object.entries(mappings)) {
    if (unifiedField && ENTITY_FIELDS.includes(unifiedField)) {
      suggested.push(sourceField);
    }
  }

  return suggested;
}

/**
 * Get field description for display in UI.
 */
export function getFieldDescription(unifiedField: string): string {
  const descriptions: Record<string, string> = {
    event_ts: "Event timestamp (required)",
    event_type: "Type or category of event (required)",
    host: "Hostname or device name",
    user: "Username or account name",
    src_ip: "Source IP address",
    dest_ip: "Destination IP address",
    src_port: "Source port number",
    dest_port: "Destination port number",
    process_name: "Process or executable name",
    process_cmdline: "Process command line arguments",
    file_path: "File path or filename",
    file_hash: "File hash (MD5, SHA256, etc.)",
    outcome: "Result or disposition (success/failure)",
    severity: "Severity or risk level",
    message: "Event message or description",
    url: "URL or URI",
    dns_query: "DNS query or domain name",
    protocol: "Network protocol",
    bytes_in: "Bytes received",
    bytes_out: "Bytes sent",
    tactic: "MITRE ATT&CK tactic",
    technique: "MITRE ATT&CK technique",
  };

  return descriptions[unifiedField] || unifiedField;
}
