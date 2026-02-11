#!/usr/bin/env python3
"""
Generate correlated sample security incident data for "Operation Midnight Access"

Scenario: Insider threat with account compromise spanning Jan 15-17, 2025
- Initial access: Attacker compromises marcus.chen's Okta credentials via phishing
- Lateral movement: Uses stolen credentials to access AWS and SSH to internal servers
- Data exfiltration: Downloads sensitive data from S3 and internal database server
"""

import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Seed for reproducibility
random.seed(42)

# ============================================================================
# SHARED ENTITIES
# ============================================================================

LEGITIMATE_USERS = {
    "sarah.kim": {
        "display_name": "Sarah Kim",
        "okta_id": "00u1a2b3c4d5e6f7g8h9",
        "role": "DevOps Engineer",
        "home_ip": "73.162.45.89",
        "ssh_key": "SHA256:Kx7pQmR9nL2vS5wT8yU3aB6cD1eF4gH7iJ0kM",
    },
    "james.taylor": {
        "display_name": "James Taylor",
        "okta_id": "00u2b3c4d5e6f7g8h9i0",
        "role": "Data Analyst",
        "home_ip": "98.45.123.67",
        "ssh_key": None,  # No SSH access
    },
    "priya.patel": {
        "display_name": "Priya Patel",
        "okta_id": "00u3c4d5e6f7g8h9i0j1",
        "role": "Security Engineer",
        "home_ip": "76.89.234.12",
        "ssh_key": "SHA256:Lm8qRnS0oP3wT6xU9yV2aB5cD4eF7gH0iJ3kN",
    },
    "alex.wong": {
        "display_name": "Alex Wong",
        "okta_id": "00u4d5e6f7g8h9i0j1k2",
        "role": "Developer",
        "home_ip": "104.28.67.99",
        "ssh_key": "SHA256:Mn9rSoT1pQ4wU7xV0yW3aB6cD5eF8gH1iJ4kO",
    },
}

COMPROMISED_USER = {
    "marcus.chen": {
        "display_name": "Marcus Chen",
        "okta_id": "00u5e6f7g8h9i0j1k2l3",
        "role": "Senior Developer",
        "home_ip": "67.183.92.44",
        "ssh_key": "SHA256:No0sTpU2qR5wV8xW1yX4aB7cD6eF9gH2iJ5kP",
    }
}

ATTACKER_IPS = {
    "185.220.101.42": {"location": "Amsterdam", "country": "Netherlands", "type": "tor_exit"},
    "91.134.156.78": {"location": "Paris", "country": "France", "type": "vps"},
    "45.33.32.156": {"location": "Frankfurt", "country": "Germany", "type": "exfil"},
}

INTERNAL_IPS = ["10.0.0.15", "10.0.0.22", "10.0.0.48", "10.0.0.67", "10.0.0.103"]

HOSTS = {
    "bastion-01": {"ip": "10.0.1.10", "type": "bastion"},
    "db-server-prod": {"ip": "10.0.2.20", "type": "database"},
    "analytics-01": {"ip": "10.0.2.30", "type": "analytics"},
    "dev-server-02": {"ip": "10.0.3.40", "type": "development"},
}

AWS_RESOURCES = {
    "buckets": ["acme-prod-data", "acme-analytics", "acme-backups", "acme-logs"],
    "instances": {
        "prod-db-01": "i-0abc123def456789a",
        "data-warehouse": "i-0bcd234efg567890b",
        "web-frontend": "i-0cde345fgh678901c",
    },
}

# Base timestamp
BASE_TIME = datetime(2025, 1, 15, 0, 0, 0)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def random_timestamp(day_offset: int, hour_range: tuple = (0, 24)) -> datetime:
    """Generate random timestamp within specified day and hour range."""
    base = BASE_TIME + timedelta(days=day_offset)
    hour = random.randint(hour_range[0], min(hour_range[1] - 1, 23))
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    micro = random.randint(0, 999999)
    return base.replace(hour=hour, minute=minute, second=second, microsecond=micro)


def format_iso(dt: datetime) -> str:
    """Format datetime as ISO string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def generate_uuid() -> str:
    """Generate a random UUID."""
    return str(uuid.uuid4())


def random_user_agent(is_attacker: bool = False) -> str:
    """Generate realistic user agent string."""
    if is_attacker:
        return random.choice([
            "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "python-requests/2.31.0",
        ])
    return random.choice([
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ])


# ============================================================================
# OKTA DATA GENERATION
# ============================================================================

def generate_okta_events() -> list[dict]:
    """Generate ~200 Okta authentication events."""
    events = []

    # Helper to add normal user activity throughout the day
    def add_daily_activity(day: int):
        """Add normal user activity for a given day."""
        for user, info in LEGITIMATE_USERS.items():
            # Morning login
            login_time = random_timestamp(day, (7, 10))
            events.append(create_okta_login(user, info, login_time, info["home_ip"], "SUCCESS"))

            # App accesses throughout the day
            apps = ["AWS SSO", "GitHub", "Jira", "Confluence", "Slack", "Datadog", "PagerDuty", "Zoom", "Box"]
            num_accesses = random.randint(6, 10)
            for _ in range(num_accesses):
                events.append(create_okta_app_access(
                    user, info,
                    random_timestamp(day, (9, 18)),
                    random.choice(apps)
                ))

            # Session refreshes
            if random.random() > 0.4:
                events.append(create_okta_session_refresh(user, info, random_timestamp(day, (11, 17))))

            # Occasional second login (after lunch, different device, etc.)
            if random.random() > 0.7:
                events.append(create_okta_login(user, info, random_timestamp(day, (13, 15)), info["home_ip"], "SUCCESS"))

    # Day 1: Jan 15 - Initial compromise
    # Normal morning logins
    for user, info in LEGITIMATE_USERS.items():
        login_time = random_timestamp(0, (7, 10))
        events.append(create_okta_login(user, info, login_time, info["home_ip"], "SUCCESS"))

        # Some users check other apps
        if random.random() > 0.5:
            events.append(create_okta_app_access(user, info, login_time + timedelta(minutes=random.randint(5, 30)), "AWS SSO"))

    # Marcus's normal morning login
    marcus_info = COMPROMISED_USER["marcus.chen"]
    marcus_morning = datetime(2025, 1, 15, 8, 15, 23, 456000)
    events.append(create_okta_login("marcus.chen", marcus_info, marcus_morning, marcus_info["home_ip"], "SUCCESS"))
    events.append(create_okta_app_access("marcus.chen", marcus_info, marcus_morning + timedelta(minutes=12), "AWS SSO"))

    # ATTACK SEQUENCE: Failed attempts from attacker
    attacker_ip = "185.220.101.42"
    attacker_geo = ATTACKER_IPS[attacker_ip]

    # 14:23 - First failed attempt
    attack_start = datetime(2025, 1, 15, 14, 23, 45, 123000)
    for i in range(5):
        events.append(create_okta_login(
            "marcus.chen", marcus_info,
            attack_start + timedelta(minutes=i, seconds=random.randint(10, 50)),
            attacker_ip, "FAILURE",
            reason="INVALID_CREDENTIALS" if i < 3 else "VERIFICATION_ERROR",
            geo=attacker_geo
        ))

    # 14:32 - Successful compromise
    compromise_time = datetime(2025, 1, 15, 14, 32, 18, 789000)
    events.append(create_okta_login(
        "marcus.chen", marcus_info, compromise_time, attacker_ip, "SUCCESS",
        geo=attacker_geo, suspicious=True
    ))

    # 14:33 - MFA push accepted (phished)
    events.append(create_okta_mfa(
        "marcus.chen", marcus_info,
        compromise_time + timedelta(seconds=45),
        attacker_ip, "SUCCESS", geo=attacker_geo
    ))

    # Attacker accesses AWS SSO
    events.append(create_okta_app_access(
        "marcus.chen", marcus_info,
        compromise_time + timedelta(minutes=5),
        "AWS SSO", attacker_ip, geo=attacker_geo
    ))

    # Normal afternoon activity from other users
    for user, info in LEGITIMATE_USERS.items():
        for _ in range(random.randint(1, 3)):
            events.append(create_okta_app_access(
                user, info,
                random_timestamp(0, (13, 18)),
                random.choice(["AWS SSO", "GitHub", "Jira", "Confluence"])
            ))

    # Day 2: Jan 16 - Lateral movement
    # Normal morning logins
    for user, info in LEGITIMATE_USERS.items():
        login_time = random_timestamp(1, (7, 10))
        events.append(create_okta_login(user, info, login_time, info["home_ip"], "SUCCESS"))

    # Attacker maintains access (early morning, different IP)
    secondary_ip = "91.134.156.78"
    secondary_geo = ATTACKER_IPS[secondary_ip]
    events.append(create_okta_login(
        "marcus.chen", marcus_info,
        datetime(2025, 1, 16, 2, 10, 33, 445000),
        secondary_ip, "SUCCESS", geo=secondary_geo
    ))
    events.append(create_okta_app_access(
        "marcus.chen", marcus_info,
        datetime(2025, 1, 16, 2, 12, 18, 221000),
        "AWS SSO", secondary_ip, geo=secondary_geo
    ))

    # Normal day activity
    for user, info in LEGITIMATE_USERS.items():
        for _ in range(random.randint(2, 5)):
            events.append(create_okta_app_access(
                user, info,
                random_timestamp(1, (9, 18)),
                random.choice(["AWS SSO", "GitHub", "Jira", "Confluence", "Slack"])
            ))

    # Session refreshes
    for user, info in list(LEGITIMATE_USERS.items())[:2]:
        events.append(create_okta_session_refresh(user, info, random_timestamp(1, (14, 17))))

    # Day 3: Jan 17 - Detection & Response
    # Normal morning
    for user, info in LEGITIMATE_USERS.items():
        events.append(create_okta_login(user, info, random_timestamp(2, (7, 10)), info["home_ip"], "SUCCESS"))

    # 08:00 - Marcus notices something wrong, requests password reset
    events.append(create_okta_password_reset(
        "marcus.chen", marcus_info,
        datetime(2025, 1, 17, 8, 0, 15, 234000),
        marcus_info["home_ip"]
    ))

    # 08:15 - Security locks account
    events.append(create_okta_account_lock(
        "marcus.chen", marcus_info,
        datetime(2025, 1, 17, 8, 15, 42, 567000),
        "priya.patel", LEGITIMATE_USERS["priya.patel"]
    ))

    # Add comprehensive daily activity for all 3 days
    for day in range(3):
        add_daily_activity(day)

    # Add some failed logins (normal typos)
    events.append(create_okta_login(
        "james.taylor", LEGITIMATE_USERS["james.taylor"],
        random_timestamp(0, (8, 9)), "98.45.123.67", "FAILURE",
        reason="INVALID_CREDENTIALS"
    ))
    events.append(create_okta_login(
        "alex.wong", LEGITIMATE_USERS["alex.wong"],
        random_timestamp(1, (8, 9)), "104.28.67.99", "FAILURE",
        reason="INVALID_CREDENTIALS"
    ))
    events.append(create_okta_login(
        "sarah.kim", LEGITIMATE_USERS["sarah.kim"],
        random_timestamp(2, (7, 8)), "73.162.45.89", "FAILURE",
        reason="INVALID_CREDENTIALS"
    ))

    # Add some MFA events for legitimate users
    for user, info in LEGITIMATE_USERS.items():
        if random.random() > 0.5:
            events.append(create_okta_mfa(
                user, info,
                random_timestamp(random.randint(0, 2), (8, 17)),
                info["home_ip"], "SUCCESS"
            ))

    # Sort by timestamp
    events.sort(key=lambda x: x["published"])
    return events


def create_okta_login(user: str, info: dict, ts: datetime, ip: str, result: str,
                      reason: str = None, geo: dict = None, suspicious: bool = False) -> dict:
    """Create an Okta login event."""
    if geo is None:
        geo = {"location": "San Francisco", "country": "United States"}

    return {
        "uuid": generate_uuid(),
        "published": format_iso(ts),
        "eventType": "user.session.start",
        "displayMessage": "User login to Okta",
        "severity": "INFO" if result == "SUCCESS" else "WARN",
        "actor.id": info["okta_id"],
        "actor.alternateId": f"{user}@acme.com",
        "actor.displayName": info["display_name"],
        "client.ipAddress": ip,
        "client.userAgent.rawUserAgent": random_user_agent(suspicious),
        "client.geographicalContext.city": geo["location"],
        "client.geographicalContext.country": geo["country"],
        "outcome.result": result,
        "outcome.reason": reason or "",
        "authenticationContext.credentialType": "PASSWORD",
        "authenticationContext.authenticationProvider": "OKTA",
        "target.0.alternateId": "Okta Dashboard",
        "debugContext.debugData.requestUri": "/api/v1/authn",
    }


def create_okta_mfa(user: str, info: dict, ts: datetime, ip: str, result: str, geo: dict = None) -> dict:
    """Create an Okta MFA event."""
    if geo is None:
        geo = {"location": "San Francisco", "country": "United States"}

    return {
        "uuid": generate_uuid(),
        "published": format_iso(ts),
        "eventType": "user.authentication.auth_via_mfa",
        "displayMessage": "Authentication of user via MFA",
        "severity": "INFO",
        "actor.id": info["okta_id"],
        "actor.alternateId": f"{user}@acme.com",
        "actor.displayName": info["display_name"],
        "client.ipAddress": ip,
        "client.userAgent.rawUserAgent": random_user_agent(),
        "client.geographicalContext.city": geo["location"],
        "client.geographicalContext.country": geo["country"],
        "outcome.result": result,
        "outcome.reason": "",
        "authenticationContext.credentialType": "OKTA_VERIFY_PUSH",
        "authenticationContext.authenticationProvider": "OKTA",
        "target.0.alternateId": f"{user}@acme.com",
        "debugContext.debugData.requestUri": "/api/v1/authn/factors/verify",
    }


def create_okta_app_access(user: str, info: dict, ts: datetime, app: str,
                           ip: str = None, geo: dict = None) -> dict:
    """Create an Okta app access event."""
    if ip is None:
        ip = info["home_ip"]
    if geo is None:
        geo = {"location": "San Francisco", "country": "United States"}

    return {
        "uuid": generate_uuid(),
        "published": format_iso(ts),
        "eventType": "user.authentication.sso",
        "displayMessage": f"User single sign on to app",
        "severity": "INFO",
        "actor.id": info["okta_id"],
        "actor.alternateId": f"{user}@acme.com",
        "actor.displayName": info["display_name"],
        "client.ipAddress": ip,
        "client.userAgent.rawUserAgent": random_user_agent(),
        "client.geographicalContext.city": geo["location"],
        "client.geographicalContext.country": geo["country"],
        "outcome.result": "SUCCESS",
        "outcome.reason": "",
        "authenticationContext.credentialType": "SESSION",
        "authenticationContext.authenticationProvider": "OKTA",
        "target.0.alternateId": app,
        "debugContext.debugData.requestUri": f"/app/{app.lower().replace(' ', '_')}/sso",
    }


def create_okta_session_refresh(user: str, info: dict, ts: datetime) -> dict:
    """Create an Okta session refresh event."""
    return {
        "uuid": generate_uuid(),
        "published": format_iso(ts),
        "eventType": "user.session.access_token",
        "displayMessage": "User session token refreshed",
        "severity": "INFO",
        "actor.id": info["okta_id"],
        "actor.alternateId": f"{user}@acme.com",
        "actor.displayName": info["display_name"],
        "client.ipAddress": info["home_ip"],
        "client.userAgent.rawUserAgent": random_user_agent(),
        "client.geographicalContext.city": "San Francisco",
        "client.geographicalContext.country": "United States",
        "outcome.result": "SUCCESS",
        "outcome.reason": "",
        "authenticationContext.credentialType": "SESSION",
        "authenticationContext.authenticationProvider": "OKTA",
        "target.0.alternateId": "Okta",
        "debugContext.debugData.requestUri": "/api/v1/sessions/me/refresh",
    }


def create_okta_password_reset(user: str, info: dict, ts: datetime, ip: str) -> dict:
    """Create an Okta password reset event."""
    return {
        "uuid": generate_uuid(),
        "published": format_iso(ts),
        "eventType": "user.account.reset_password",
        "displayMessage": "User requested password reset",
        "severity": "WARN",
        "actor.id": info["okta_id"],
        "actor.alternateId": f"{user}@acme.com",
        "actor.displayName": info["display_name"],
        "client.ipAddress": ip,
        "client.userAgent.rawUserAgent": random_user_agent(),
        "client.geographicalContext.city": "San Francisco",
        "client.geographicalContext.country": "United States",
        "outcome.result": "SUCCESS",
        "outcome.reason": "",
        "authenticationContext.credentialType": "PASSWORD",
        "authenticationContext.authenticationProvider": "OKTA",
        "target.0.alternateId": f"{user}@acme.com",
        "debugContext.debugData.requestUri": "/api/v1/users/me/credentials/forgot_password",
    }


def create_okta_account_lock(user: str, info: dict, ts: datetime,
                             admin_user: str, admin_info: dict) -> dict:
    """Create an Okta account lock event."""
    return {
        "uuid": generate_uuid(),
        "published": format_iso(ts),
        "eventType": "user.lifecycle.suspend",
        "displayMessage": "User account suspended",
        "severity": "WARN",
        "actor.id": admin_info["okta_id"],
        "actor.alternateId": f"{admin_user}@acme.com",
        "actor.displayName": admin_info["display_name"],
        "client.ipAddress": admin_info["home_ip"],
        "client.userAgent.rawUserAgent": random_user_agent(),
        "client.geographicalContext.city": "San Francisco",
        "client.geographicalContext.country": "United States",
        "outcome.result": "SUCCESS",
        "outcome.reason": "Security incident response",
        "authenticationContext.credentialType": "SESSION",
        "authenticationContext.authenticationProvider": "OKTA",
        "target.0.alternateId": f"{user}@acme.com",
        "debugContext.debugData.requestUri": "/api/v1/users/lifecycle/suspend",
    }


# ============================================================================
# CLOUDTRAIL DATA GENERATION
# ============================================================================

def generate_cloudtrail_events() -> list[dict]:
    """Generate ~200 CloudTrail events."""
    events = []

    # Helper to add daily normal AWS activity
    def add_daily_aws_activity(day: int):
        """Add normal AWS activity for a given day."""
        for user, info in LEGITIMATE_USERS.items():
            if user in ["sarah.kim", "priya.patel"]:  # AWS admin users
                # EC2 operations
                for _ in range(random.randint(3, 6)):
                    events.append(create_cloudtrail_ec2(
                        user, random_timestamp(day, (8, 18)), info["home_ip"]
                    ))
                # S3 operations
                for _ in range(random.randint(5, 10)):
                    events.append(create_cloudtrail_s3(
                        user, random_timestamp(day, (8, 18)), info["home_ip"],
                        random.choice(["GetObject", "PutObject", "GetObject", "GetObject"])
                    ))
                # IAM queries (normal admin tasks)
                if random.random() > 0.5:
                    events.append(create_cloudtrail_iam(
                        user, random_timestamp(day, (9, 17)), info["home_ip"],
                        random.choice(["GetUser", "ListUsers", "GetRole"])
                    ))

            if user == "james.taylor":  # Data analyst - read access
                for _ in range(random.randint(4, 8)):
                    events.append(create_cloudtrail_s3(
                        user, random_timestamp(day, (9, 17)), info["home_ip"], "GetObject",
                        bucket="acme-analytics"
                    ))

            if user == "alex.wong":  # Developer - some S3 and EC2
                for _ in range(random.randint(2, 5)):
                    events.append(create_cloudtrail_s3(
                        user, random_timestamp(day, (9, 18)), info["home_ip"],
                        random.choice(["GetObject", "PutObject"]),
                        bucket=random.choice(["acme-prod-data", "acme-backups"])
                    ))

    # Day 1: Jan 15 - Normal activity + initial reconnaissance
    # Normal morning activity
    for user, info in LEGITIMATE_USERS.items():
        if user in ["sarah.kim", "priya.patel"]:  # AWS admin users
            # EC2 operations
            for _ in range(random.randint(2, 4)):
                events.append(create_cloudtrail_ec2(
                    user, random_timestamp(0, (8, 12)), info["home_ip"]
                ))
            # S3 operations
            for _ in range(random.randint(3, 6)):
                events.append(create_cloudtrail_s3(
                    user, random_timestamp(0, (9, 17)), info["home_ip"], "GetObject"
                ))
        if user == "james.taylor":  # Data analyst - read access
            for _ in range(random.randint(2, 4)):
                events.append(create_cloudtrail_s3(
                    user, random_timestamp(0, (9, 17)), info["home_ip"], "GetObject",
                    bucket="acme-analytics"
                ))

    # Marcus normal activity
    marcus_info = COMPROMISED_USER["marcus.chen"]
    events.append(create_cloudtrail_s3(
        "marcus.chen", datetime(2025, 1, 15, 9, 23, 15), marcus_info["home_ip"], "GetObject"
    ))
    events.append(create_cloudtrail_s3(
        "marcus.chen", datetime(2025, 1, 15, 10, 45, 33), marcus_info["home_ip"], "PutObject"
    ))

    # ATTACK: Post-compromise reconnaissance (15:01+)
    attacker_ip = "185.220.101.42"

    # AssumeRole to DevOps
    events.append(create_cloudtrail_assume_role(
        "marcus.chen", datetime(2025, 1, 15, 15, 1, 22, 456000),
        attacker_ip, "DevOpsRole"
    ))

    # ListBuckets
    events.append(create_cloudtrail_s3_list(
        "marcus.chen", datetime(2025, 1, 15, 15, 15, 8, 789000), attacker_ip
    ))

    # Describe instances
    events.append(create_cloudtrail_ec2_describe(
        "marcus.chen", datetime(2025, 1, 15, 15, 20, 45), attacker_ip
    ))

    # Initial data access attempts
    for i in range(3):
        events.append(create_cloudtrail_s3(
            "marcus.chen",
            datetime(2025, 1, 15, 15, 30 + i*2, random.randint(0, 59)),
            attacker_ip, "GetObject", bucket="acme-prod-data"
        ))

    # Day 2: Jan 16 - Bulk data access
    secondary_ip = "91.134.156.78"

    # Early morning bulk downloads
    bulk_start = datetime(2025, 1, 16, 2, 18, 0)
    sensitive_keys = [
        "exports/customer-db.sql",
        "exports/user-credentials-backup.csv",
        "exports/financial-q4.xlsx",
        "backups/prod-db-2025-01-14.sql.gz",
        "analytics/user-behavior-raw.parquet",
    ]

    for i, key in enumerate(sensitive_keys):
        events.append(create_cloudtrail_s3(
            "marcus.chen",
            bulk_start + timedelta(minutes=i*2, seconds=random.randint(0, 59)),
            secondary_ip, "GetObject",
            bucket="acme-prod-data", key=key
        ))

    # More bulk downloads (50+ objects attack pattern)
    for i in range(45):
        events.append(create_cloudtrail_s3(
            "marcus.chen",
            datetime(2025, 1, 16, 10, 30, 0) + timedelta(seconds=i*15 + random.randint(0, 10)),
            secondary_ip, "GetObject",
            bucket="acme-prod-data",
            key=f"data/segment_{i:03d}.json"
        ))

    # Normal activity from other users
    for user, info in LEGITIMATE_USERS.items():
        if user in ["sarah.kim", "priya.patel"]:
            for _ in range(random.randint(3, 6)):
                events.append(create_cloudtrail_s3(
                    user, random_timestamp(1, (9, 17)), info["home_ip"],
                    random.choice(["GetObject", "PutObject"])
                ))
            for _ in range(random.randint(1, 3)):
                events.append(create_cloudtrail_ec2(
                    user, random_timestamp(1, (9, 17)), info["home_ip"]
                ))

    # IAM queries by attacker
    events.append(create_cloudtrail_iam(
        "marcus.chen", datetime(2025, 1, 16, 2, 25, 33), secondary_ip, "ListUsers"
    ))
    events.append(create_cloudtrail_iam(
        "marcus.chen", datetime(2025, 1, 16, 2, 26, 18), secondary_ip, "ListRoles"
    ))
    events.append(create_cloudtrail_iam(
        "marcus.chen", datetime(2025, 1, 16, 2, 27, 45), secondary_ip, "GetUser"
    ))

    # Day 3: Jan 17 - Exfiltration attempt & detection
    exfil_ip = "45.33.32.156"

    # Attempted cross-account copy (blocked)
    events.append(create_cloudtrail_s3(
        "marcus.chen", datetime(2025, 1, 17, 1, 30, 22),
        exfil_ip, "PutObject",
        bucket="external-bucket-attacker",
        error="AccessDenied", error_msg="Access Denied"
    ))
    events.append(create_cloudtrail_s3(
        "marcus.chen", datetime(2025, 1, 17, 1, 32, 15),
        exfil_ip, "CopyObject",
        error="AccessDenied", error_msg="Cross-account access denied"
    ))

    # Normal morning activity
    for user, info in LEGITIMATE_USERS.items():
        if user in ["sarah.kim", "priya.patel"]:
            for _ in range(random.randint(2, 4)):
                events.append(create_cloudtrail_s3(
                    user, random_timestamp(2, (8, 12)), info["home_ip"], "GetObject"
                ))

    # Add comprehensive daily activity for all 3 days
    for day in range(3):
        add_daily_aws_activity(day)

    # Console logins
    for user, info in LEGITIMATE_USERS.items():
        for day in range(3):
            if random.random() > 0.4:
                events.append(create_cloudtrail_console_login(
                    user, random_timestamp(day, (8, 10)), info["home_ip"]
                ))

    # Sort by timestamp
    events.sort(key=lambda x: x["eventTime"])
    return events


def create_cloudtrail_s3(user: str, ts: datetime, ip: str, action: str,
                         bucket: str = None, key: str = None,
                         error: str = None, error_msg: str = None) -> dict:
    """Create a CloudTrail S3 event."""
    if bucket is None:
        bucket = random.choice(AWS_RESOURCES["buckets"])
    if key is None:
        key = f"data/{random.choice(['report', 'export', 'backup', 'log'])}_{random.randint(1, 100)}.json"

    event = {
        "eventTime": format_iso(ts),
        "eventVersion": "1.08",
        "eventSource": "s3.amazonaws.com",
        "eventName": action,
        "eventType": "AwsApiCall",
        "awsRegion": "us-east-1",
        "sourceIPAddress": ip,
        "userIdentity.type": "IAMUser",
        "userIdentity.userName": user,
        "userIdentity.arn": f"arn:aws:iam::123456789012:user/{user}",
        "userAgent": random.choice(["aws-cli/2.15.0 Python/3.11.6", "Boto3/1.34.0", "console.amazonaws.com"]),
        "requestParameters.bucketName": bucket,
        "requestParameters.key": key,
        "requestParameters.instanceId": "",
        "responseElements.requestId": generate_uuid()[:16].upper(),
        "errorCode": error or "",
        "errorMessage": error_msg or "",
        "recipientAccountId": "123456789012",
    }
    return event


def create_cloudtrail_s3_list(user: str, ts: datetime, ip: str) -> dict:
    """Create a CloudTrail ListBuckets event."""
    return {
        "eventTime": format_iso(ts),
        "eventVersion": "1.08",
        "eventSource": "s3.amazonaws.com",
        "eventName": "ListBuckets",
        "eventType": "AwsApiCall",
        "awsRegion": "us-east-1",
        "sourceIPAddress": ip,
        "userIdentity.type": "IAMUser",
        "userIdentity.userName": user,
        "userIdentity.arn": f"arn:aws:iam::123456789012:user/{user}",
        "userAgent": "aws-cli/2.15.0 Python/3.11.6",
        "requestParameters.bucketName": "",
        "requestParameters.key": "",
        "requestParameters.instanceId": "",
        "responseElements.requestId": generate_uuid()[:16].upper(),
        "errorCode": "",
        "errorMessage": "",
        "recipientAccountId": "123456789012",
    }


def create_cloudtrail_ec2(user: str, ts: datetime, ip: str) -> dict:
    """Create a CloudTrail EC2 event."""
    instance_name, instance_id = random.choice(list(AWS_RESOURCES["instances"].items()))
    action = random.choice(["DescribeInstances", "StartInstances", "StopInstances"])

    return {
        "eventTime": format_iso(ts),
        "eventVersion": "1.08",
        "eventSource": "ec2.amazonaws.com",
        "eventName": action,
        "eventType": "AwsApiCall",
        "awsRegion": "us-east-1",
        "sourceIPAddress": ip,
        "userIdentity.type": "IAMUser",
        "userIdentity.userName": user,
        "userIdentity.arn": f"arn:aws:iam::123456789012:user/{user}",
        "userAgent": "console.amazonaws.com",
        "requestParameters.bucketName": "",
        "requestParameters.key": "",
        "requestParameters.instanceId": instance_id,
        "responseElements.requestId": generate_uuid()[:16].upper(),
        "errorCode": "",
        "errorMessage": "",
        "recipientAccountId": "123456789012",
    }


def create_cloudtrail_ec2_describe(user: str, ts: datetime, ip: str) -> dict:
    """Create a CloudTrail EC2 DescribeInstances event."""
    return {
        "eventTime": format_iso(ts),
        "eventVersion": "1.08",
        "eventSource": "ec2.amazonaws.com",
        "eventName": "DescribeInstances",
        "eventType": "AwsApiCall",
        "awsRegion": "us-east-1",
        "sourceIPAddress": ip,
        "userIdentity.type": "IAMUser",
        "userIdentity.userName": user,
        "userIdentity.arn": f"arn:aws:iam::123456789012:user/{user}",
        "userAgent": "aws-cli/2.15.0 Python/3.11.6",
        "requestParameters.bucketName": "",
        "requestParameters.key": "",
        "requestParameters.instanceId": "",
        "responseElements.requestId": generate_uuid()[:16].upper(),
        "errorCode": "",
        "errorMessage": "",
        "recipientAccountId": "123456789012",
    }


def create_cloudtrail_assume_role(user: str, ts: datetime, ip: str, role: str) -> dict:
    """Create a CloudTrail AssumeRole event."""
    return {
        "eventTime": format_iso(ts),
        "eventVersion": "1.08",
        "eventSource": "sts.amazonaws.com",
        "eventName": "AssumeRole",
        "eventType": "AwsApiCall",
        "awsRegion": "us-east-1",
        "sourceIPAddress": ip,
        "userIdentity.type": "IAMUser",
        "userIdentity.userName": user,
        "userIdentity.arn": f"arn:aws:iam::123456789012:user/{user}",
        "userAgent": "aws-cli/2.15.0 Python/3.11.6",
        "requestParameters.bucketName": "",
        "requestParameters.key": "",
        "requestParameters.instanceId": "",
        "responseElements.requestId": generate_uuid()[:16].upper(),
        "errorCode": "",
        "errorMessage": "",
        "recipientAccountId": "123456789012",
    }


def create_cloudtrail_iam(user: str, ts: datetime, ip: str, action: str) -> dict:
    """Create a CloudTrail IAM event."""
    return {
        "eventTime": format_iso(ts),
        "eventVersion": "1.08",
        "eventSource": "iam.amazonaws.com",
        "eventName": action,
        "eventType": "AwsApiCall",
        "awsRegion": "us-east-1",
        "sourceIPAddress": ip,
        "userIdentity.type": "IAMUser",
        "userIdentity.userName": user,
        "userIdentity.arn": f"arn:aws:iam::123456789012:user/{user}",
        "userAgent": "aws-cli/2.15.0 Python/3.11.6",
        "requestParameters.bucketName": "",
        "requestParameters.key": "",
        "requestParameters.instanceId": "",
        "responseElements.requestId": generate_uuid()[:16].upper(),
        "errorCode": "",
        "errorMessage": "",
        "recipientAccountId": "123456789012",
    }


def create_cloudtrail_console_login(user: str, ts: datetime, ip: str) -> dict:
    """Create a CloudTrail ConsoleLogin event."""
    return {
        "eventTime": format_iso(ts),
        "eventVersion": "1.08",
        "eventSource": "signin.amazonaws.com",
        "eventName": "ConsoleLogin",
        "eventType": "AwsConsoleSignIn",
        "awsRegion": "us-east-1",
        "sourceIPAddress": ip,
        "userIdentity.type": "IAMUser",
        "userIdentity.userName": user,
        "userIdentity.arn": f"arn:aws:iam::123456789012:user/{user}",
        "userAgent": "Mozilla/5.0",
        "requestParameters.bucketName": "",
        "requestParameters.key": "",
        "requestParameters.instanceId": "",
        "responseElements.requestId": generate_uuid()[:16].upper(),
        "errorCode": "",
        "errorMessage": "",
        "recipientAccountId": "123456789012",
    }


# ============================================================================
# SSH DATA GENERATION
# ============================================================================

def generate_ssh_events() -> list[dict]:
    """Generate ~200 SSH authentication events."""
    events = []
    pid_counter = 10000
    session_counter = 1000

    # Helper to add daily SSH activity
    def add_daily_ssh_activity(day: int):
        nonlocal pid_counter, session_counter
        for user, info in LEGITIMATE_USERS.items():
            if info["ssh_key"] is None:
                continue

            # Multiple SSH sessions throughout the day
            num_sessions = random.randint(2, 5)
            for _ in range(num_sessions):
                pid_counter += 1
                session_counter += 1
                host = random.choice(list(HOSTS.keys()))
                start_time = random_timestamp(day, (8, 20))

                events.append(create_ssh_auth_success(
                    user, start_time, host, info["home_ip"],
                    info["ssh_key"], pid_counter, f"sess_{session_counter:06d}"
                ))
                events.append(create_ssh_session_opened(
                    user, start_time + timedelta(seconds=1), host, pid_counter
                ))

                # Most sessions close eventually
                if random.random() > 0.2:
                    events.append(create_ssh_session_closed(
                        user, start_time + timedelta(hours=random.randint(1, 8)),
                        host, pid_counter
                    ))

    # Day 1: Jan 15 - Normal activity + initial SSH access
    # Normal SSH from legitimate users
    for user, info in LEGITIMATE_USERS.items():
        if info["ssh_key"] is None:
            continue  # james.taylor has no SSH access

        # Morning SSH sessions
        for host in random.sample(list(HOSTS.keys()), random.randint(1, 2)):
            pid_counter += 1
            session_counter += 1
            start_time = random_timestamp(0, (8, 12))

            events.append(create_ssh_auth_success(
                user, start_time, host, info["home_ip"],
                info["ssh_key"], pid_counter, f"sess_{session_counter:06d}"
            ))
            events.append(create_ssh_session_opened(
                user, start_time + timedelta(seconds=1), host, pid_counter
            ))

            # Session close later
            if random.random() > 0.3:
                events.append(create_ssh_session_closed(
                    user, start_time + timedelta(hours=random.randint(1, 4)),
                    host, pid_counter
                ))

    # Marcus normal SSH in morning
    marcus_info = COMPROMISED_USER["marcus.chen"]
    pid_counter += 1
    session_counter += 1
    events.append(create_ssh_auth_success(
        "marcus.chen", datetime(2025, 1, 15, 9, 30, 15),
        "dev-server-02", marcus_info["home_ip"],
        marcus_info["ssh_key"], pid_counter, f"sess_{session_counter:06d}"
    ))
    events.append(create_ssh_session_opened(
        "marcus.chen", datetime(2025, 1, 15, 9, 30, 16),
        "dev-server-02", pid_counter
    ))
    events.append(create_ssh_session_closed(
        "marcus.chen", datetime(2025, 1, 15, 12, 45, 33),
        "dev-server-02", pid_counter
    ))

    # ATTACK: 16:00 - Failed password attempt (attacker doesn't have key initially)
    attacker_ip = "185.220.101.42"
    pid_counter += 1
    events.append(create_ssh_auth_failure(
        "marcus.chen", datetime(2025, 1, 15, 16, 0, 23),
        "bastion-01", attacker_ip, "password", pid_counter
    ))
    events.append(create_ssh_auth_failure(
        "marcus.chen", datetime(2025, 1, 15, 16, 0, 45),
        "bastion-01", attacker_ip, "password", pid_counter + 1
    ))

    # 16:02 - Attacker gets in with key (must have extracted it)
    pid_counter += 2
    session_counter += 1
    events.append(create_ssh_auth_success(
        "marcus.chen", datetime(2025, 1, 15, 16, 2, 18),
        "bastion-01", attacker_ip,
        marcus_info["ssh_key"], pid_counter, f"sess_{session_counter:06d}"
    ))
    events.append(create_ssh_session_opened(
        "marcus.chen", datetime(2025, 1, 15, 16, 2, 19),
        "bastion-01", pid_counter
    ))

    # Day 2: Jan 16 - Lateral movement
    secondary_ip = "91.134.156.78"

    # 02:15 - Attacker pivots to db-server-prod via bastion
    pid_counter += 1
    session_counter += 1
    events.append(create_ssh_auth_success(
        "marcus.chen", datetime(2025, 1, 16, 2, 15, 33),
        "db-server-prod", "10.0.1.10",  # From bastion internal IP
        marcus_info["ssh_key"], pid_counter, f"sess_{session_counter:06d}"
    ))
    events.append(create_ssh_session_opened(
        "marcus.chen", datetime(2025, 1, 16, 2, 15, 34),
        "db-server-prod", pid_counter
    ))

    # Session to analytics-01
    pid_counter += 1
    session_counter += 1
    events.append(create_ssh_auth_success(
        "marcus.chen", datetime(2025, 1, 16, 11, 0, 22),
        "analytics-01", "10.0.1.10",
        marcus_info["ssh_key"], pid_counter, f"sess_{session_counter:06d}"
    ))
    events.append(create_ssh_session_opened(
        "marcus.chen", datetime(2025, 1, 16, 11, 0, 23),
        "analytics-01", pid_counter
    ))

    # Normal activity from other users
    for user, info in LEGITIMATE_USERS.items():
        if info["ssh_key"] is None:
            continue

        for _ in range(random.randint(2, 4)):
            pid_counter += 1
            session_counter += 1
            host = random.choice(list(HOSTS.keys()))
            start_time = random_timestamp(1, (8, 18))

            events.append(create_ssh_auth_success(
                user, start_time, host, info["home_ip"],
                info["ssh_key"], pid_counter, f"sess_{session_counter:06d}"
            ))
            events.append(create_ssh_session_opened(
                user, start_time + timedelta(seconds=1), host, pid_counter
            ))

            if random.random() > 0.4:
                events.append(create_ssh_session_closed(
                    user, start_time + timedelta(hours=random.randint(1, 6)),
                    host, pid_counter
                ))

    # Add comprehensive daily SSH activity for all 3 days
    for day in range(3):
        add_daily_ssh_activity(day)

    # Some brute force attempts (random attacker noise - common internet background noise)
    brute_force_users = ["root", "admin", "ubuntu", "test", "user", "oracle", "postgres", "mysql", "guest"]
    for _ in range(20):
        pid_counter += 1
        events.append(create_ssh_auth_failure(
            random.choice(brute_force_users),
            random_timestamp(random.randint(0, 2), (0, 24)),
            random.choice(["bastion-01", "db-server-prod"]),
            f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "password", pid_counter
        ))

    # Invalid user attempts (attackers trying common usernames)
    invalid_users = ["administrator", "deploy", "jenkins", "backup", "www-data", "nginx", "docker"]
    for invalid_user in random.sample(invalid_users, 4):
        pid_counter += 1
        events.append(create_ssh_invalid_user(
            invalid_user, random_timestamp(random.randint(0, 2), (0, 24)),
            "bastion-01",
            f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            pid_counter
        ))

    # Day 3: Jan 17 - Detection
    # 08:20 - Sessions terminated
    events.append(create_ssh_disconnect(
        "marcus.chen", datetime(2025, 1, 17, 8, 20, 15),
        "bastion-01", 10050, "administrator disconnect"
    ))
    events.append(create_ssh_disconnect(
        "marcus.chen", datetime(2025, 1, 17, 8, 20, 18),
        "db-server-prod", 10052, "administrator disconnect"
    ))
    events.append(create_ssh_disconnect(
        "marcus.chen", datetime(2025, 1, 17, 8, 20, 22),
        "analytics-01", 10054, "administrator disconnect"
    ))

    # Normal morning activity
    for user, info in LEGITIMATE_USERS.items():
        if info["ssh_key"] is None:
            continue

        pid_counter += 1
        session_counter += 1
        host = random.choice(list(HOSTS.keys()))
        start_time = random_timestamp(2, (8, 12))

        events.append(create_ssh_auth_success(
            user, start_time, host, info["home_ip"],
            info["ssh_key"], pid_counter, f"sess_{session_counter:06d}"
        ))
        events.append(create_ssh_session_opened(
            user, start_time + timedelta(seconds=1), host, pid_counter
        ))

    # Sort by timestamp
    events.sort(key=lambda x: x["timestamp"])
    return events


def create_ssh_auth_success(user: str, ts: datetime, host: str, ip: str,
                            key_fp: str, pid: int, session_id: str) -> dict:
    """Create SSH successful authentication event."""
    return {
        "timestamp": format_iso(ts),
        "hostname": host,
        "program": "sshd",
        "pid": str(pid),
        "message": f"Accepted publickey for {user} from {ip} port {random.randint(40000, 65000)} ssh2: {key_fp}",
        "auth_method": "publickey",
        "username": user,
        "source_ip": ip,
        "source_port": str(random.randint(40000, 65000)),
        "ssh_protocol": "SSH-2.0-OpenSSH_8.9",
        "key_fingerprint": key_fp,
        "session_id": session_id,
        "event_type": "auth_success",
    }


def create_ssh_auth_failure(user: str, ts: datetime, host: str, ip: str,
                            method: str, pid: int) -> dict:
    """Create SSH failed authentication event."""
    return {
        "timestamp": format_iso(ts),
        "hostname": host,
        "program": "sshd",
        "pid": str(pid),
        "message": f"Failed {method} for {user} from {ip} port {random.randint(40000, 65000)} ssh2",
        "auth_method": method,
        "username": user,
        "source_ip": ip,
        "source_port": str(random.randint(40000, 65000)),
        "ssh_protocol": "SSH-2.0-OpenSSH_8.9",
        "key_fingerprint": "",
        "session_id": "",
        "event_type": "auth_failure",
    }


def create_ssh_session_opened(user: str, ts: datetime, host: str, pid: int) -> dict:
    """Create SSH session opened event."""
    return {
        "timestamp": format_iso(ts),
        "hostname": host,
        "program": "sshd",
        "pid": str(pid),
        "message": f"pam_unix(sshd:session): session opened for user {user}",
        "auth_method": "",
        "username": user,
        "source_ip": "",
        "source_port": "",
        "ssh_protocol": "",
        "key_fingerprint": "",
        "session_id": "",
        "event_type": "session_opened",
    }


def create_ssh_session_closed(user: str, ts: datetime, host: str, pid: int) -> dict:
    """Create SSH session closed event."""
    return {
        "timestamp": format_iso(ts),
        "hostname": host,
        "program": "sshd",
        "pid": str(pid),
        "message": f"pam_unix(sshd:session): session closed for user {user}",
        "auth_method": "",
        "username": user,
        "source_ip": "",
        "source_port": "",
        "ssh_protocol": "",
        "key_fingerprint": "",
        "session_id": "",
        "event_type": "session_closed",
    }


def create_ssh_invalid_user(user: str, ts: datetime, host: str, ip: str, pid: int) -> dict:
    """Create SSH invalid user event."""
    return {
        "timestamp": format_iso(ts),
        "hostname": host,
        "program": "sshd",
        "pid": str(pid),
        "message": f"Invalid user {user} from {ip} port {random.randint(40000, 65000)}",
        "auth_method": "password",
        "username": user,
        "source_ip": ip,
        "source_port": str(random.randint(40000, 65000)),
        "ssh_protocol": "SSH-2.0-OpenSSH_8.9",
        "key_fingerprint": "",
        "session_id": "",
        "event_type": "invalid_user",
    }


def create_ssh_disconnect(user: str, ts: datetime, host: str, pid: int, reason: str) -> dict:
    """Create SSH disconnect event."""
    return {
        "timestamp": format_iso(ts),
        "hostname": host,
        "program": "sshd",
        "pid": str(pid),
        "message": f"Disconnected from user {user}: {reason}",
        "auth_method": "",
        "username": user,
        "source_ip": "",
        "source_port": "",
        "ssh_protocol": "",
        "key_fingerprint": "",
        "session_id": "",
        "event_type": "disconnect",
    }


# ============================================================================
# MAIN
# ============================================================================

def write_csv(filename: str, events: list[dict], output_dir: Path):
    """Write events to CSV file."""
    if not events:
        print(f"Warning: No events to write for {filename}")
        return

    output_path = output_dir / filename
    fieldnames = list(events[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

    print(f"Wrote {len(events)} events to {output_path}")


def main():
    # Determine output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "sample_data"
    output_dir.mkdir(exist_ok=True)

    print("Generating sample security incident data...")
    print("=" * 60)
    print("Scenario: Operation Midnight Access")
    print("Timeline: January 15-17, 2025")
    print("=" * 60)

    # Generate events
    print("\nGenerating Okta authentication events...")
    okta_events = generate_okta_events()
    write_csv("okta_auth.csv", okta_events, output_dir)

    print("\nGenerating CloudTrail events...")
    cloudtrail_events = generate_cloudtrail_events()
    write_csv("cloudtrail_logs.csv", cloudtrail_events, output_dir)

    print("\nGenerating SSH authentication events...")
    ssh_events = generate_ssh_events()
    write_csv("ssh_auth.csv", ssh_events, output_dir)

    print("\n" + "=" * 60)
    print("Sample data generation complete!")
    print(f"Output directory: {output_dir}")
    print("\nKey entities to search for:")
    print("  - Compromised user: marcus.chen")
    print("  - Attacker IPs: 185.220.101.42, 91.134.156.78, 45.33.32.156")
    print("  - Attack timeline: Jan 15 14:32 (initial compromise)")


if __name__ == "__main__":
    main()
