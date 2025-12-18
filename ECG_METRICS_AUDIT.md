# ECG Clinical Metrics Audit: GE/Philips Calculation Logic

This document details the exact clinical calculation logic used in the application for ECG metrics auditing, adhering to GE Marquette and Philips clinical standards.

## 1. Core Principles
- **Median Beat Analysis**: All interval and amplitude measurements (PR, QRS, QT, Axis, RV5/SV1) are derived from an aligned **Median Beat** built from 8–12 clean beats.
- **Raw Data Only**: Calculations use the raw ADC signal before display filters (0.5–35Hz) to prevent phase shift and amplitude attenuation.
- **TP Baseline**: The isoelectric reference is the **TP segment** (700–800 ms after R-peak in the 1.3s template), subtracted from the signal before any area or peak measurement.

---

## 2. Basic Intervals (Time-Based)

### RR Interval (ms)
- **Method**: Median of differences between consecutive R-peaks over a 10-second window.
- **Formula**: `RR = median(ΔR_peaks) * (1000 / fs)`

### Heart Rate (HR, BPM)
- **Method**: Instantaneous heart rate derived from the median RR interval.
- **Formula**: `HR = 60000 / RR_ms`

### PR Interval (ms)
- **Method**: Time from P-wave onset to QRS onset on the median beat.
- **Logic**:
  - P-onset: First point between R-250ms and R-100ms where signal deviates >5% from TP baseline.
  - QRS-onset: First point before R-peak where signal deviates >5% from TP baseline.
- **Formula**: `PR = QRS_onset_ms - P_onset_ms`

### QRS Duration (ms)
- **Method**: Time from QRS onset to QRS offset (J-point) on the median beat.
- **Logic**:
  - QRS-onset: Point where signal leaves baseline before R.
  - QRS-offset (J-point): Point where signal returns to baseline after R/S wave.
- **Formula**: `QRS = QRS_offset_ms - QRS_onset_ms`

---

## 3. QT & Corrected QT (QTc)

### QT Interval (ms)
- **Method**: QRS onset to T-wave offset on the median beat.
- **Boundary Discipline**: T-offset is detected where the signal either crosses the TP baseline or the energy drops to the noise floor (0.5 * threshold).
- **Formula**: `QT = T_offset_ms - QRS_onset_ms`

### QTc (Bazett's Formula)
- **Use Case**: Standard clinical correction.
- **Formula**: `QTc = QT_sec / √RR_sec`
- **Implementation**: `qtc_ms = (QT_ms / 1000) / sqrt(RR_ms / 1000) * 1000`

### QTcF (Fridericia's Formula)
- **Use Case**: Preferred for high/low heart rates to avoid over/under-correction.
- **Formula**: `QTcF = QT_sec / (RR_sec)^(1/3)`
- **Implementation**: `qtcf_ms = (QT_ms / 1000) / (RR_ms / 1000)^(1/3) * 1000`

---

## 4. Electrical Axis (Vectorcardiography)

### Calculation Method: Area Integration
Instead of simple peak amplitudes, the axis is calculated using the **Net Area (Integral)** of the waves in Lead I and Lead aVF. This is more robust against noise and biphasic waves.

1.  **Baseline Correction**: `Signal_Corrected = Median_Beat - TP_Baseline`
2.  **Integration**: `Net_Area = ∫ (Signal_Corrected) dt` (using Trapezoidal rule `np.trapz`)
3.  **Vector Calculation**: `Axis_Rad = atan2(Net_aVF, Net_I)`
4.  **Normalization**: `Axis_Deg = (Axis_Rad * 180 / π)` normalized to 0–360°.

### Fixed Wave Windows (Relative to R-peak)
- **P-Axis**: `[-200 ms, -140 ms]` (Strict window to avoid QRS energy).
- **QRS-Axis**: `[-50 ms, +80 ms]`
- **T-Axis**: `[+120 ms, +500 ms]`

### Safety Gate (Energy Threshold)
- If `|Net_I| + |Net_aVF| < 4e-5 mV·s` (for P) or `2e-5 mV·s` (for QRS/T), the calculation is suppressed to prevent reporting axis on noise.

---

## 5. Hypertrophy Metrics (Sokolow-Lyon)

### RV5 (mV)
- **Method**: Maximum positive R-wave amplitude in Lead V5 relative to its TP baseline on the median beat.
- **Formula**: `RV5 = (max(V5_QRS_segment) - TP_Baseline_V5) / ADC_Gain_V5`

### SV1 (mV)
- **Method**: S-wave nadir (most negative point) in Lead V1 relative to its TP baseline on the median beat.
- **Formula**: `SV1 = (min(V1_QRS_segment) - TP_Baseline_V1) / ADC_Gain_V1`
- *Note: Reported as a negative value if below baseline.*

### RV5 + SV1 (Sokolow-Lyon Index)
- **Method**: Sum of magnitudes for Left Ventricular Hypertrophy (LVH) screening.
- **Formula**: `Total = RV5 + |SV1|` (Clinical threshold for LVH is typically > 3.5 mV).

---

## 6. ST Segment (mV)

### ST Deviation
- **Method**: Amplitude measured at **J + 60 ms** relative to TP baseline.
- **Formula**: `ST = (Signal(J+60ms) - TP_Baseline) / 1200.0`
- **Range**: Clamped to `[-2.0, 2.0] mV` for clinical reporting.

