# Cloud JSON Data Structure

This document describes the JSON data structure that is sent to the cloud when ECG reports are uploaded.

## Overview

When an ECG report is generated, the following data is sent to the cloud:

1. **PDF Report File** - The actual ECG report PDF
2. **JSON Twin File** (if exists) - A JSON file with the same name as the PDF (e.g., `ECG_Report_20251118_131634.json`)
3. **Metadata** - Additional metadata attached to the upload

## 1. Upload Metadata

When uploading to cloud (AWS S3, Azure, GCS, API, etc.), the following metadata is attached:

```json
{
  "filename": "ECG_Report_20251118_131634.pdf",
  "uploaded_at": "2025-11-18T13:16:34.123456",
  "file_size": 123456,
  "file_type": ".pdf",
  "patient_name": "John Doe",
  "patient_age": "45",
  "report_date": "2025-11-18 13:16:34",
  "machine_serial": "ECG-12345",
  "heart_rate": "75"
}
```

**Source:** `src/ecg/ecg_report_generator.py` lines 1758-1764

## 2. Metrics JSON Structure

The metrics are saved to `reports/metrics.json` with the following structure:

```json
{
  "timestamp": "2025-11-18 13:16:34",
  "file": "/absolute/path/to/ECG_Report_20251118_131634.pdf",
  "HR_bpm": 75,
  "PR_ms": 160,
  "QRS_ms": 90,
  "QT_ms": 400,
  "QTc_ms": 420,
  "QTcF_ms": 410,
  "ST_ms": -0.05,
  "ST_mV": -0.05,
  "RR_ms": 800,
  "Sokolow_Lyon_mV": 2.5,
  "P_QRS_T_axes_deg": ["45", "30", "60"],
  "RV5_SV1_mV": [1.5, -1.0]
}
```

**Source:** `src/ecg/ecg_report_generator.py` lines 1700-1715

## 3. Index JSON Structure

The full report data (including patient info) is saved to `reports/index.json`:

```json
{
  "timestamp": "2025-11-18 13:16:34",
  "file": "/absolute/path/to/ECG_Report_20251118_131634.pdf",
  "patient": {
    "name": "John Doe",
    "age": "45",
    "gender": "Male",
    "date_time": "2025-11-18 13:16:34"
  },
  "metrics": {
    "HR_bpm": 75,
    "PR_ms": 160,
    "QRS_ms": 90,
    "QT_ms": 400,
    "QTc_ms": 420,
    "QTcF_ms": 410,
    "ST_ms": -0.05,
    "ST_mV": -0.05,
    "RR_ms": 800,
    "Sokolow_Lyon_mV": 2.5,
    "P_QRS_T_axes_deg": ["45", "30", "60"],
    "RV5_SV1_mV": [1.5, -1.0]
  }
}
```

**Source:** `src/ecg/ecg_report_generator.py` lines 1655-1678

## 4. JSON Twin File (If Created)

If a JSON twin file exists (same name as PDF but with `.json` extension), it would contain the same structure as the `index.json` entry above. Currently, the code checks for this file but doesn't create it automatically.

**Source:** `src/ecg/ecg_report_generator.py` lines 1774-1781

## 5. API Upload Format

When uploading to a custom API endpoint, the data is sent as:

**Request:**
- **Method:** POST
- **Headers:**
  - `Authorization: Bearer <api_key>` (if configured)
- **Body (multipart/form-data):**
  - `file`: The PDF/JSON file (binary)
  - `metadata`: JSON string containing the metadata structure above

**Source:** `src/utils/cloud_uploader.py` lines 596-630

## 6. S3 Upload Format

When uploading to AWS S3:

- **Bucket:** Configured via `AWS_S3_BUCKET`
- **Key/Path:** `ecg-reports/YYYY/MM/DD/filename.pdf`
- **Metadata:** Attached as S3 object metadata (all key-value pairs from upload_metadata)
- **URL Format:** `https://{bucket}.s3.{region}.amazonaws.com/{key}`

**Source:** `src/utils/cloud_uploader.py` lines 413-448

## 7. Field Descriptions

| Field | Type | Description | Units |
|-------|------|-------------|-------|
| `HR_bpm` | integer | Heart Rate | beats per minute |
| `PR_ms` | integer | PR Interval | milliseconds |
| `QRS_ms` | integer | QRS Duration | milliseconds |
| `QT_ms` | integer | QT Interval | milliseconds |
| `QTc_ms` | integer | Corrected QT (Bazett's) | milliseconds |
| `QTcF_ms` | integer | Corrected QT (Fridericia's) | milliseconds |
| `ST_ms` | float | ST Segment | milliseconds |
| `ST_mV` | float | ST Segment | millivolts |
| `RR_ms` | integer | RR Interval | milliseconds |
| `Sokolow_Lyon_mV` | float | Sokolow-Lyon Index (RV5 + SV1) | millivolts |
| `P_QRS_T_axes_deg` | array[string] | P, QRS, T axes | degrees |
| `RV5_SV1_mV` | array[float] | RV5 and SV1 amplitudes | millivolts |

## 8. Upload Log Structure

Uploads are logged to `reports/upload_log.json`:

```json
{
  "local_path": "/path/to/ECG_Report_20251118_131634.pdf",
  "uploaded_at": "2025-11-18T13:16:34.123456",
  "service": "s3",
  "result": {
    "status": "success",
    "service": "s3",
    "url": "https://bucket.s3.region.amazonaws.com/ecg-reports/2025/11/18/ECG_Report_20251118_131634.pdf",
    "key": "ecg-reports/2025/11/18/ECG_Report_20251118_131634.pdf",
    "bucket": "bucket-name"
  },
  "metadata": {
    "filename": "ECG_Report_20251118_131634.pdf",
    "uploaded_at": "2025-11-18T13:16:34.123456",
    "file_size": 123456,
    "file_type": ".pdf",
    "patient_name": "John Doe",
    "patient_age": "45",
    "report_date": "2025-11-18 13:16:34",
    "machine_serial": "ECG-12345",
    "heart_rate": "75"
  }
}
```

**Source:** `src/utils/cloud_uploader.py` lines 708-733

## Notes

- The system prevents duplicate uploads by checking the upload log
- Only PDF and JSON report files are uploaded (not logs, temp files, etc.)
- Metadata is filtered to only include allowed keys when uploading
- All timestamps are in ISO 8601 format
- File paths are stored as absolute paths

