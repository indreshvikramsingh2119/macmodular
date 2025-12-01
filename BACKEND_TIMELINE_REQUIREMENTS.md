## Multi-Backend Roadmap

Scope covers three device-specific services (CPAP/BiPAP, Oxygen Concentrator, ECG) plus the shared orchestrator layer that routes requests by serial number. Each backend keeps its own datastore/IaC but follows the same release cadence.

---

## 1. CPAP/BiPAP Telemetry Backend

- **Current stack**: Node.js 18, Express, MongoDB (Atlas), Mongoose models `DeviceData`/`DeviceConfig`, AWS IoT Core ingestion, MQTT + `aws-iot-device-sdk-v2`.
- **Core requirements**  
  - Auth via JWT (Cognito or custom).  
  - Telemetry ingest from IoT rules, persistence in MongoDB, retention policies.  
  - Configuration push endpoints, firmware OTA hooks.  
  - Admin dashboards (pagination, filtering) exposed to orchestrator.  
  - Alerting hooks → SNS/Webhooks.
- **Representative payloads**

  ```json
  {
    "serial": "CPAP-2301-9912",
    "timestamp": "2025-11-24T10:15:32Z",
    "metrics": {
      "pressure_cm_h2o": 12.4,
      "respiratory_rate": 18,
      "leak_rate_lpm": 24.1,
      "patient_mode": "AutoCPAP"
    },
    "firmware": "v4.2.1"
  }
  ```

  ```json
  {
    "serial": "CPAP-2301-9912",
    "config": {
      "target_pressure": 12,
      "humidity_level": 3,
      "alerts": {
        "leak_threshold": 30,
        "rr_low": 10,
        "rr_high": 26
      }
    }
  }
  ```

- **Estimated effort**
  - Enhancements & orchestrator integration: **2 weeks** (stabilize APIs, add serial registry hooks, document contracts).
  - Testing (unit + integration + IoT soak): **4 working days**.

---

## 2. Oxygen Concentrator Backend (new)

- **Proposed stack**: Node.js 18 + Express (TypeScript), PostgreSQL (RDS) via Prisma, AWS IoT Core ingestion, S3 for report blobs, Redis for rate limiting/queues.
- **Core requirements**  
  - Serial-number registration & ownership workflow.  
  - Metrics ingest (flow rate, oxygen purity, alarms) via MQTT/HTTPS.  
  - Config commands (flow adjustments, maintenance reminders).  
  - REST + WebSocket endpoints for orchestrator/mobile apps.  
  - Audit logging + alert pipelines.
- **Representative payloads**

  ```json
  {
    "serial": "OXY-8844-5521",
    "timestamp": "2025-11-24T10:22:07Z",
    "metrics": {
      "oxygen_purity_pct": 94.6,
      "flow_rate_lpm": 2.5,
      "temperature_c": 37.2,
      "battery_pct": 82,
      "alarm_code": null
    },
    "status": "online"
  }
  ```

  ```json
  {
    "serial": "OXY-8844-5521",
    "config": {
      "flow_rate_lpm": 3.0,
      "night_mode": true,
      "maintenance_due_date": "2026-01-15"
    }
  }
  ```

- **Estimated effort**
  - Build net-new backend + infra: **5 weeks** (Week 1 scaffold + DB, Week 2 auth/config, Week 3 telemetry ingest, Week 4 IoT + alerts, Week 5 hardening & docs).
  - Testing (unit, integration, IoT soak, mobile acceptance): **1.5 weeks** embedded within schedule (approx. 6 working days).

---

## 3. ECG Backend (new)

- **Proposed stack**: Node.js 18 + Express or Fastify (TypeScript), PostgreSQL + TimescaleDB extension for time-series metrics, S3 for PDFs, Redis for caching, WebSocket for live streams.
- **Core requirements**  
  - User auth + RBAC, device linking via serial numbers.  
  - Report upload: receive PDF/JSON, store metadata, push file to S3.  
  - Metrics API (heart rate, HRV, arrhythmia flags) with pagination.  
  - Admin endpoints & analytics for clinicians.  
  - Integration with desktop PyQt app and orchestrator service.
- **Representative payloads**

  ```json
  {
    "serial": "ECG-7711-0045",
    "timestamp": "2025-11-24T10:30:11Z",
    "metrics": {
      "heart_rate_bpm": 78,
      "qrs_ms": 92,
      "qt_ms": 380,
      "arrhythmia": "none",
      "signal_quality": "good"
    },
    "lead": "II"
  }
  ```

  ```json
  {
    "serial": "ECG-7711-0045",
    "report": {
      "report_id": "rpt_893445",
      "s3_url": "s3://ecg-reports/2025/11/24/rpt_893445.pdf",
      "summary": {
        "avg_hr": 76,
        "max_hr": 112,
        "min_hr": 58,
        "alerts": ["PVC detected"]
      }
    }
  }
  ```

- **Estimated effort**
  - Full implementation + AWS deployment: **5 weeks** (same breakdown as earlier FastAPI estimate, adapted for Express/TS if preferred).  
  - Testing (API unit, load, mobile/desktop integration, S3 flow): **1 week** inside the 5-week plan.

---

## Cross-Cutting Testing Matrix

| Stage | CPAP/BiPAP | Oxygen | ECG | Notes |
| --- | --- | --- | --- | --- |
| Unit tests | 2 days | 3 days | 3 days | Jest/Mocha suites; TypeScript typing for new services |
| Integration/API | 1 day | 2 days | 2 days | Postman/Newman or k6; focus on serial routing |
| IoT soak/field | 1 day | 2 days | 2 days | MQTT load, disconnect/reconnect, firmware updates |
| Mobile/Orchestrator acceptance | 0.5 day | 1 day | 1 day | Validate add-device, data views, permissions |

Totals align with per-service estimates above (≈4 days CPAP, 6 days Oxygen, 5 days ECG).

---

## Dependencies & Deliverables

- **Serial registry & orchestrator** must be in place before mobile apps can switch to unified flows.
- **Contracts**: publish OpenAPI specs + JSON schemas for each payload, versioned per service.
- **Environments**: Dev (Docker), Staging (AWS test accounts), Prod (ECS/RDS/S3/IoT). CI/CD uses GitHub Actions → ECR → ECS blue/green.
- **Documentation**: runbooks per backend, onboarding guide for mobile developers, payload reference shared with OEM partners.

---

## Timeline Snapshot (calendar weeks)

| Week | CPAP/BiPAP | Oxygen | ECG | Orchestrator |
| --- | --- | --- | --- | --- |
| 1 | API/contract cleanup | Scaffold + DB schema | Scaffold + DB schema | Registry model, auth |
| 2 | Serial registry integration | Auth + config endpoints | Auth + report upload | Routing middleware |
| 3 | Alerting polish | Telemetry ingest + IoT | Metrics + WebSocket | Aggregation APIs |
| 4 | Load tests + docs | Alerts + dashboards | Admin + analytics | Mobile endpoints |
| 5 | Release + monitor | Hardening + release | Hardening + release | Cross-service QA |

Adjust sequencing if teams run in parallel; oxygen + ECG streams can overlap once orchestrator primitives exist.


