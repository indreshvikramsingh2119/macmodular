# Standardized ECG Calculations - Clinical Compliance

## Overview

All ECG calculations have been standardized to follow **GE Marquette / Philips clinical standards** for consistency and accuracy.

---

## ✅ Standardized Calculations

### 1. PR Interval

**Function**: `measure_pr_from_median_beat()` in `clinical_measurements.py`

**Standard**: P onset → QRS onset (GE/Philips standard)

**Method**:
- Uses median beat (8-12 beats)
- Detects P-wave bounds using `detect_p_wave_bounds()`
- Finds QRS onset using threshold-based detection
- PR = QRS onset - P onset

**Valid Range**: 100-300 ms

**Location**: `src/ecg/clinical_measurements.py:480-511`

---

### 2. QRS Duration

**Function**: `measure_qrs_duration_from_median_beat()` in `clinical_measurements.py`

**Standard**: QRS onset → J-point (GE/Philips standard)

**Method**:
- Uses median beat (8-12 beats)
- Finds QRS onset using threshold-based detection
- Finds J-point (end of S-wave) at minimum of QRS segment
- QRS duration = J-point - QRS onset

**Valid Range**: 40-200 ms

**Location**: `src/ecg/clinical_measurements.py:514-548`

---

### 3. QT Interval

**Function**: `measure_qt_from_median_beat()` in `clinical_measurements.py`

**Standard**: QRS onset → T offset (GE/Philips standard)

**Method**:
- Uses median beat (8-12 beats)
- Finds QRS onset using threshold-based detection
- Finds T-peak (max absolute deflection after QRS)
- Finds T-offset (signal returns to TP baseline)
- QT = T offset - QRS onset

**Valid Range**: 200-650 ms

**Location**: `src/ecg/clinical_measurements.py:235-307`

---

### 4. QTc (Corrected QT) - **BAZETT'S FORMULA**

**Function**: `calculate_qtc_interval()` in `twelve_lead_test.py`

**Formula**: **QTc = QT / √(RR)**

Where:
- QT in seconds
- RR in seconds (calculated from heart rate: RR = 60 / HR)

**Implementation**:
```python
rr_interval = 60.0 / heart_rate  # RR in seconds
qt_sec = qt_interval / 1000.0    # QT in seconds
qtc = qt_sec / np.sqrt(rr_interval)  # Bazett's formula
qtc_ms = int(round(qtc * 1000))  # Convert back to ms
```

**Display**: Always labeled as **"QTCB (Bazett)"** in reports

**Location**: `src/ecg/twelve_lead_test.py:2846-2870`

**Report Display**: `src/ecg/ecg_report_generator.py:1399` - Shows "QTCB (Bazett)"

---

### 5. QTcF (Fridericia)

**Function**: `calculate_qtcf_interval()` in `twelve_lead_test.py`

**Formula**: **QTcF = QT / RR^(1/3)**

**Display**: Labeled as **"QTCF (Fridericia)"** in reports

**Location**: `src/ecg/twelve_lead_test.py:2872-2898`

---

### 6. ST Deviation

**Function**: `measure_st_deviation_from_median_beat()` in `clinical_measurements.py`

**Standard**: J+60ms measurement (GE/Philips standard)

**Method**:
- Uses median beat (8-12 beats)
- Finds J-point (end of S-wave)
- Measures ST at J + 60ms
- ST deviation = ST point - TP baseline

**Units**: mV (millivolts)

**Valid Range**: -2.0 to +2.0 mV

**Location**: `src/ecg/clinical_measurements.py:380-423`

**Report Display**: Labeled as **"ST Deviation (J+60 ms)"**

---

### 7. Electrical Axis (P/QRS/T)

**Function**: `calculate_axis_from_median_beat()` in `clinical_measurements.py`

**Standard**: Area-based method using Lead I and aVF (GE/Philips standard)

**Method**:
- Uses median beat (8-12 beats)
- Wave-specific TP baseline correction
- Net area integration (not peak-based)
- Axis = atan2(net_aVF, net_I) × 180/π
- Normalized to -180° to +180°

**Location**: `src/ecg/clinical_measurements.py:551-660`

**Report Display**: Shows P/QRS/T axes in degrees

---

## 📊 Report Display Standards

### Observation Table Format

All reports display metrics in standardized format:

| Metric | Display Format | Standard Range |
|--------|---------------|----------------|
| PR Interval | `XXX ms` | 120-200 ms |
| QRS Complex | `XXX ms` | 70-120 ms |
| QRS Axis | `XX°` | Normal |
| QT Interval | `XXX ms` | 300-450 ms |
| **QTCB (Bazett)** | `XXX ms` | 300-450 ms |
| QTCF (Fridericia) | `X.XXX s` | 300-450 ms |
| ST Deviation (J+60 ms) | `X.XX` (no units) | Normal |

**Key Points**:
- ✅ QTc is **always** labeled as "QTCB (Bazett)" to indicate Bazett's formula
- ✅ ST deviation shows numeric value only (no "mV" suffix)
- ✅ All intervals in milliseconds (ms)
- ✅ QTcF shown in seconds (s) format

---

## 🔄 Integration Points

### ECG Test Page

**File**: `src/ecg/twelve_lead_test.py`

**Function**: `calculate_ecg_metrics()`

All calculations use standardized functions:

```python
# PR Interval (standardized)
pr_interval = measure_pr_from_median_beat(median_beat_ii, time_axis, fs, tp_baseline_ii)

# QRS Duration (standardized)
qrs_duration = measure_qrs_duration_from_median_beat(median_beat_ii, time_axis, fs, tp_baseline_ii)

# QT Interval (standardized)
qt_interval = measure_qt_from_median_beat(median_beat_ii, time_axis, fs, tp_baseline_ii)

# QTc (Bazett's formula)
qtc_interval = self.calculate_qtc_interval(heart_rate, qt_interval)

# ST Deviation (standardized)
st_segment = measure_st_deviation_from_median_beat(median_beat_ii, time_axis, fs, tp_baseline_ii, j_offset_ms=60)
```

---

## ✅ Validation

All calculations are validated against clinical standards:

1. **Range Validation**: All measurements checked against valid clinical ranges
2. **Baseline Correction**: TP baseline subtraction before all measurements
3. **Median Beat**: All calculations use 8-12 beat median for stability
4. **Formula Verification**: QTc uses exact Bazett's formula: `QT / √(RR)`

---

## 📝 Summary

✅ **PR Interval**: Standardized - P onset to QRS onset  
✅ **QRS Duration**: Standardized - QRS onset to J-point  
✅ **QT Interval**: Standardized - QRS onset to T offset  
✅ **QTc**: **Bazett's formula** - `QT / √(RR)` - Clearly labeled in reports  
✅ **ST Deviation**: Standardized - J+60ms measurement  
✅ **Axis**: Standardized - Area-based method using Lead I and aVF  

All calculations follow **GE Marquette / Philips clinical standards** for consistency and accuracy.

