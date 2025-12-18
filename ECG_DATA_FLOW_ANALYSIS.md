# ECG Data Flow Analysis - Clinical vs Display Separation

## 🔍 Data Flow Trace

### 1. Raw ECG Data Sources

**Hardware/Serial Mode:**
- Location: `twelve_lead_test.py:6469-6472`
- Data stored in: `self.data[i]` (circular buffer)
- Processing: Only smoothing applied (`apply_realtime_smoothing`)
- Status: ✅ RAW - No display processing

**Demo Mode:**
- Location: `demo_manager.py:492-494`
- Data stored in: `self.ecg_test_page.data[lead_index]`
- Processing: Baseline centering only (`centered_value = float(value) - baseline`)
- Status: ✅ RAW - Minimal processing (baseline subtraction only)

### 2. Clinical Analysis Functions

**Heart Rate Calculation:**
- Function: `calculate_heart_rate(lead_data)` (line 1888)
- Data source: `self.data[1]` (Lead II raw buffer)
- Called from: `calculate_ecg_metrics()` (line 1865)
- Status: ✅ CORRECT - Uses raw `self.data[1]`

**ECG Metrics Calculation:**
- Function: `calculate_ecg_metrics()` (line 1836)
- Data source: `self.data[1]` (Lead II raw buffer)
- Calculates: HR, PR, QRS, QRS Axis, ST, QT, QTc
- Status: ✅ CORRECT - Uses raw `self.data[1]`

**RR Interval Calculation:**
- Location: `calculate_heart_rate()` (line 2034)
- Data source: R-peaks detected from `lead_data` (which is `self.data[1]`)
- Status: ✅ CORRECT - Uses raw data

**PR/QRS/QT/QTc Calculation:**
- Functions: `calculate_pr_interval()`, `calculate_qrs_duration()`, `calculate_qt_interval()`, `calculate_qtc_interval()`
- Data source: `self.data[1]` (Lead II raw buffer)
- Status: ✅ CORRECT - Uses raw data

### 3. Display Processing

**12-Lead Display (Demo Mode):**
- Location: `update_plots()` (line 6405-6440)
- Processing: 
  - `raw = np.asarray(self.data[i])` - Creates COPY
  - `raw = raw - np.nanmean(raw)` - Baseline correction (on copy)
  - `raw = raw * gain` - Gain application (on copy)
  - Window extraction: `src = raw[-window_len:]` (on copy)
  - Resampling for display (on copy)
- Status: ✅ CORRECT - Works on copy, `self.data` unchanged

**12-Lead Display (Serial Mode):**
- Location: `update_plots()` (line 6559-6621)
- Processing:
  - `raw_data = self.data[i]` - Reference (but not modified)
  - `data_slice = raw_data[-samples_to_show:]` - Creates COPY
  - `filtered_slice = data_slice - np.mean(data_slice)` - Baseline correction (on copy)
  - AC filter applied (on copy)
  - Gain applied (on copy)
- Status: ✅ CORRECT - Works on copy, `self.data` unchanged

**Expanded Lead View:**
- Location: `expanded_lead_view.py:1146-1173`
- Processing:
  - `window_signal = self.ecg_data[start_idx:end_idx]` - Creates COPY
  - `window_signal_filtered = window_signal - np.mean(window_signal)` - Baseline correction (on copy)
  - Gain and amplification applied (on copy)
- Status: ✅ CORRECT - Works on copy, `self.ecg_data` unchanged

## ⚠️ POTENTIAL ISSUES FOUND

### Issue #1: Demo Mode Baseline Centering in Data Buffer
**Location:** `demo_manager.py:490-494`
```python
baseline = self._baseline_means.get(lead_index, 0.0)
centered_value = float(value) - baseline
self.ecg_test_page.data[lead_index][-1] = centered_value
```

**Problem:** Baseline centering is applied directly to `self.data`, which is then used for clinical analysis.

**Impact:** 
- If baseline centering changes over time, it could affect R-peak detection
- Clinical measurements use this "centered" data, not true raw data

**Fix Required:** Store raw values in `self.data`, apply centering only for display.

### Issue #2: Expanded View Uses `self.ecg_data` (Source Unknown)
**Location:** `expanded_lead_view.py:1146`
```python
window_signal = self.ecg_data[start_idx:end_idx]
```

**Problem:** Need to verify where `self.ecg_data` comes from and if it's raw or processed.

**Status:** ⚠️ NEEDS VERIFICATION

## ✅ VERIFICATION CHECKLIST

- [x] `calculate_heart_rate()` uses `self.data[1]` directly
- [x] `calculate_ecg_metrics()` uses `self.data[1]` directly  
- [x] Display processing in `update_plots()` works on copies
- [x] `self.data` is not modified by display processing
- [ ] Demo mode baseline centering - NEEDS FIX
- [ ] Expanded view data source - NEEDS VERIFICATION

## 🔧 RECOMMENDED FIXES

### Fix #1: Separate Raw and Display Data in Demo Mode
Store raw values in `self.data`, apply centering only for display.

### Fix #2: Verify Expanded View Data Source
Ensure `self.ecg_data` in expanded view is raw, not display-processed.

### Fix #3: Add Explicit Separation
Create clear variable names:
- `clinical_ecg_data` - for analysis
- `display_ecg_data` - for rendering


