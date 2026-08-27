# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import random
from typing import Any

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore
from google.genai import types


MODEL = "gemini-3.6-flash"

# CRITICAL: Hardcode project ID as a literal string to avoid Agent Platform project number issue
PROJECT_ID = "qwiklabs-gcp-03-d36c5051a70a"

# In-memory circular log stream buffer for recent telemetry readings
SENSOR_LOG_BUFFER: list[dict[str, Any]] = []


def get_firestore_client() -> firestore.Client:
    """Returns a Firestore client initialized with explicit project ID string."""
    return firestore.Client(project=PROJECT_ID)


def generate_sensor_telemetry() -> dict[str, Any]:
    """Generates random telemetry log values for Sensor 1 (Temperature), Sensor 2 (Humidity), and Sensor 3 (Air Quality)
    specifically tuned to frequently trigger alert actions and threshold flags.

    Returns:
        Dictionary containing sensor_1_temp_f, sensor_2_humidity_pct, sensor_3_air_quality, timestamp, and alerts.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Generate random test telemetry values tuned to trigger threshold breaches
    temp_f = round(random.uniform(77.0, 96.0), 1)
    humidity_pct = round(random.uniform(35.0, 68.0), 1)
    air_quality = random.choice(["Good", "Moderate", "Poor", "Poor"])

    # Evaluate threshold flags
    flags = []
    if temp_f >= 80.0:
        flags.append({
            "sensor": "Sensor 1 (Temperature)",
            "flag_code": "TEMP_HIGH_FLAG",
            "value": f"{temp_f}°F",
            "threshold": ">= 80.0°F",
            "message": f"🚨 ALERT: Sensor 1 Temperature reached {temp_f}°F! Flashing Flag Triggered.",
            "severity": "CRITICAL",
        })

    if humidity_pct >= 40.0:
        flags.append({
            "sensor": "Sensor 2 (Humidity)",
            "flag_code": "HUMIDITY_HIGH_FLAG",
            "value": f"{humidity_pct}%",
            "threshold": ">= 40.0%",
            "message": f"⚠️ ALERT: Sensor 2 Humidity reached {humidity_pct}%! Flashing Flag Triggered.",
            "severity": "WARNING",
        })

    if air_quality.upper() == "POOR":
        flags.append({
            "sensor": "Sensor 3 (Air Quality)",
            "flag_code": "AIR_QUALITY_POOR_FLAG",
            "value": air_quality,
            "threshold": "== Poor",
            "message": f"💨 ALERT: Sensor 3 Air Quality is POOR! Hazard Flashing Flag Triggered.",
            "severity": "CRITICAL",
        })

    telemetry_doc = {
        "timestamp": timestamp,
        "sensor_1_temp_f": temp_f,
        "sensor_2_humidity_pct": humidity_pct,
        "sensor_3_air_quality": air_quality,
        "active_flags_count": len(flags),
        "flags": flags,
    }

    # Record to in-memory stream buffer
    SENSOR_LOG_BUFFER.insert(0, telemetry_doc)
    if len(SENSOR_LOG_BUFFER) > 50:
        SENSOR_LOG_BUFFER.pop()

    # Automatically dispatch & write incidents to Firestore backend
    if flags:
        try:
            db = get_firestore_client()
            for flag in flags:
                incident_id = f"INC-{random.randint(10000, 99999)}"
                db.collection("incidents").document(incident_id).set({
                    "incident_id": incident_id,
                    "sensor": flag["sensor"],
                    "error_code": flag["flag_code"],
                    "severity": flag["severity"],
                    "status": "OPEN",
                    "summary": flag["message"],
                    "details": f"Reading: {flag['value']} vs Threshold: {flag['threshold']}",
                    "created_at": timestamp,
                })
        except Exception as e:
            print(f"Firestore incident write note: {e}")

    return telemetry_doc


def fetch_sensor_logs(count: int = 10) -> list[dict]:
    """Fetches recent sensor log telemetry entries from the active stream.

    Args:
        count: Number of recent log items to return (default 10).

    Returns:
        List of recent telemetry log dictionaries.
    """
    if not SENSOR_LOG_BUFFER:
        generate_sensor_telemetry()
    return SENSOR_LOG_BUFFER[:count]


def evaluate_sensor_thresholds(
    temperature_f: float,
    humidity_pct: float,
    air_quality: str,
) -> dict[str, Any]:
    """Evaluates sensor parameters against defined alert thresholds and returns active alert flags.

    Args:
        temperature_f: Sensor 1 Temperature value in Fahrenheit (Alert threshold >= 80.0°F).
        humidity_pct: Sensor 2 Humidity percentage (Alert threshold >= 40.0%).
        air_quality: Sensor 3 Air Quality rating ('Good', 'Moderate', 'Poor' -> Alert on 'Poor').

    Returns:
        Evaluation summary dictionary with active flags and status.
    """
    flags = []
    if temperature_f >= 80.0:
        flags.append({
            "flag_id": "FLAG_TEMP_80F",
            "sensor": "Sensor 1 (Temperature)",
            "severity": "HIGH",
            "message": f"Temperature reached {temperature_f}°F (Threshold: >= 80°F)",
        })

    if humidity_pct >= 40.0:
        flags.append({
            "flag_id": "FLAG_HUMIDITY_40PCT",
            "sensor": "Sensor 2 (Humidity)",
            "severity": "MEDIUM",
            "message": f"Humidity reached {humidity_pct}% (Threshold: >= 40%)",
        })

    if air_quality.strip().lower() == "poor":
        flags.append({
            "flag_id": "FLAG_AIR_QUALITY_POOR",
            "sensor": "Sensor 3 (Air Quality)",
            "severity": "HIGH",
            "message": "Air Quality is POOR! Hazard alert raised.",
        })

    return {
        "status": "EVALUATED",
        "has_active_flags": len(flags) > 0,
        "flag_count": len(flags),
        "flags": flags,
    }


def fetch_incidents_from_db(status: str = "all") -> list[dict]:
    """Fetches incident records from the Firestore 'incidents' collection.

    Args:
        status: Filter by incident status ('OPEN', 'INVESTIGATING', 'RESOLVED', or 'all').

    Returns:
        List of incident records stored in Firestore.
    """
    db = get_firestore_client()
    query = db.collection("incidents")

    docs = query.stream()
    incidents = []
    for doc in docs:
        data = doc.to_dict()
        if status != "all" and data.get("status", "").upper() != status.upper():
            continue
        incidents.append(data)
    return incidents


async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an expert IoT Sensor Monitoring & Flashing Alert Agent with a Firestore backend. "
        "You monitor 3 periodic sensors: Sensor 1 (Temperature), Sensor 2 (Humidity), and Sensor 3 (Air Quality). "
        "Threshold rules:\n"
        "1. Temperature >= 80°F -> Raise Flashing Temp Alert Flag.\n"
        "2. Humidity >= 40% -> Raise Flashing Humidity Alert Flag.\n"
        "3. Air Quality == 'Poor' -> Raise Flashing Air Quality Alert Flag.\n"
        "Use `generate_sensor_telemetry`, `fetch_sensor_logs`, `evaluate_sensor_thresholds`, and `fetch_incidents_from_db` "
        "to analyze sensor telemetry, evaluate threshold flags, notify users, and manage Firestore incidents."
    ),
    tools=[
        generate_sensor_telemetry,
        fetch_sensor_logs,
        evaluate_sensor_thresholds,
        fetch_incidents_from_db,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)



