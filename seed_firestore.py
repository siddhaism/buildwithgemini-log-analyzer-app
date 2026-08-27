# Copyright 2026 Google LLC
# Seed script for Firestore collection 'incidents'

from google.cloud import firestore

# CRITICAL: Hardcode project ID as a literal string to avoid Agent Platform project number issue
PROJECT_ID = "qwiklabs-gcp-03-d36c5051a70a"

SEED_INCIDENTS = [
    {
        "incident_id": "INC-10001",
        "service": "db-cluster",
        "error_code": "DB_CONNECTION_TIMEOUT",
        "severity": "CRITICAL",
        "status": "OPEN",
        "summary": "Connection to PostgreSQL master instance timed out after 30000ms.",
        "details": "Host: 10.0.4.12:5432. Connection pool exhausted under heavy load.",
        "channel": "#oncall-devops",
        "created_at": "2026-08-27 21:15:00 UTC",
    },
    {
        "incident_id": "INC-10002",
        "service": "payment-gateway",
        "error_code": "PAYMENT_GATEWAY_504",
        "severity": "ERROR",
        "status": "INVESTIGATING",
        "summary": "Upstream Stripe API returned 504 Gateway Timeout during checkout charge.",
        "details": "Retried 3 times with exponential backoff before failing transaction.",
        "channel": "#oncall-devops",
        "created_at": "2026-08-27 21:15:42 UTC",
    },
    {
        "incident_id": "INC-10003",
        "service": "api-gateway",
        "error_code": "OUT_OF_MEMORY_KILLED",
        "severity": "CRITICAL",
        "status": "RESOLVED",
        "summary": "Container api-gateway-pod-77x OOMKilled.",
        "details": "Memory limit 2Gi exceeded. Pod restarted with memory limit increased to 4Gi.",
        "channel": "#oncall-devops",
        "created_at": "2026-08-27 21:17:05 UTC",
    },
]

def seed_database():
    print(f"Connecting to Firestore with project ID: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("incidents")

    for incident in SEED_INCIDENTS:
        doc_ref = collection_ref.document(incident["incident_id"])
        doc_ref.set(incident)
        print(f"✓ Seeded incident {incident['incident_id']} for service '{incident['service']}' (status: {incident['status']})")

    print("✅ Firestore seeding complete!")

if __name__ == "__main__":
    seed_database()
