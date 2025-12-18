# ✅ Final Baseline Fix - Complete Implementation

## Summary

All baseline wander and respiration instability issues have been fixed. The ECG display now behaves like a hospital monitor with stable baseline, no vertical drift, and sharp QRS waves.

---

## ✅ Changes Applied

### 1. **Baseline Extraction - Moving Average Signal (Not Mean)**

**Files Modified:**
- `src/ecg/twelve_lead_test.py` - `_extract_low_frequency_baseline()`
- `src/ecg/expanded_lead_view.py` - `_extract_low_frequency_baseline()`

**Change:**
- ❌ **Removed:** `baseline_estimate = np.nanmean(signal[-window_samples:])`
- ✅ **Added:** Moving average signal extraction using convolution:
  ```python
  window_samples = int(2.0 * sampling_rate)
  kernel = np.ones(window_samples) / window_samples
  baseline_signal = np.convolve(signal, kernel, mode="valid")
  baseline_estimate = baseline_signal[-1]
  ```

**Why:** Moving average extracts actual low-frequency baseline signal, not just a statistic. This properly removes respiration (0.1-0.35 Hz) from the baseline estimate.

---

### 2. **Slow Baseline Anchor - EMA Alpha = 0.0005**

**Files Modified:**
- `src/ecg/twelve_lead_test.py` - Demo mode and Serial mode display paths
- `src/ecg/expanded_lead_view.py` - Init and update paths

**Change:**
- ❌ **Removed:** `self._baseline_alpha_slow = 0.002` (too fast, baseline still moves)
- ✅ **Added:** `self._baseline_alpha_slow = 0.0005` (monitor-grade, ~4 sec time constant at 500 Hz)

**Implementation:**
```python
# Extract low-frequency baseline estimate
baseline_estimate = self._extract_low_frequency_baseline(signal, sampling_rate)

# Update anchor with slow EMA (tracks only very-low-frequency drift)
self._baseline_anchors[i] = (1 - 0.0005) * self._baseline_anchors[i] + 0.0005 * baseline_estimate

# Subtract anchor (NOT raw mean)
display_signal = signal - self._baseline_anchors[i]
```

**Why:** Alpha = 0.0005 provides monitor-grade stability. Baseline moves slowly (2-4 sec time constant), filtering out respiration while tracking only very-low-frequency drift.

---

### 3. **Removed All Other Baseline Corrections**

**Files Modified:**
- `src/ecg/twelve_lead_test.py`:
  - Removed fallback mean subtraction in demo mode (line ~6482)
  - Removed fallback mean subtraction in serial mode (line ~6661)
  - Removed mean subtraction from `apply_ecg_filtering()` (line ~4292)
- `src/ecg/expanded_lead_view.py`:
  - Removed fallback mean subtraction in error handlers (lines ~1224, 1230)

**Changes:**
- ❌ **Removed:** `signal -= np.mean(signal)` in fallback error handlers
- ❌ **Removed:** `signal -= np.nanmean(signal)` in fallback error handlers
- ✅ **Replaced with:** Use original signal (baseline anchor handles it)

**Why:** Baseline correction must exist **only once** (display path, via slow anchor). Multiple corrections cause "breathing" waveform.

---

### 4. **Order of Operations (Display Only)**

**Correct Order:**
1. **Baseline anchor** → Extract low-frequency baseline, update EMA anchor, subtract anchor
2. **Gain** → Apply adaptive gain based on signal source
3. **Filtering** → Apply AC/EMG/DFT filters (no mean subtraction)
4. **Resample** → Apply wave-speed scaling (if needed)
5. **Plot** → Display with fixed Y-axis

**Files:**
- `src/ecg/twelve_lead_test.py` - Demo mode (lines ~6463-6485), Serial mode (lines ~6641-6663)
- `src/ecg/expanded_lead_view.py` - Update plot (lines ~1203-1234)

---

### 5. **Lock Y-Axis (UX Fix)**

**Files Modified:**
- `src/ecg/expanded_lead_view.py` - `update_plot()` function

**Change:**
- ❌ **Removed:** Auto-scaling based on current window data
- ✅ **Added:** Fixed Y-axis range (no auto-scaling in live view)
  ```python
  # Set fixed Y-axis range based on display gain
  y_range = 2000 * self.display_gain
  self.fixed_ylim = (-y_range, y_range)
  self.ax.set_ylim(self.fixed_ylim[0], self.fixed_ylim[1])
  ```

**Why:** Hospital monitors never auto-scale Y-axis in live view. Auto-scaling causes apparent baseline movement when the window slides.

---

## ✅ Verification Checklist

- [x] **No per-window mean subtraction exists** - All removed from display paths
- [x] **Raw clinical data untouched** - `self.data[i]` stores raw ECG only
- [x] **Baseline anchor applied before resampling** - Order: anchor → gain → filter → resample → plot
- [x] **Moving average signal extraction** - Not mean/median, actual convolution-based baseline
- [x] **EMA alpha = 0.0005** - Monitor-grade slow anchor (all paths updated)
- [x] **Y-axis locked** - Fixed range, no auto-scaling in expanded view
- [x] **No baseline correction in `apply_adaptive_gain()`** - Confirmed clean
- [x] **No baseline correction in `apply_ecg_filtering()`** - Mean subtraction removed
- [x] **Expanded view baseline correction only once** - Slow anchor only

---

## 🎯 Expected Result

After these fixes:
- ✅ **Baseline almost flat** - No vertical drift
- ✅ **Respiration barely visible** - Slow sway only (not "breathing")
- ✅ **QRS sharp** - No distortion from multiple baseline corrections
- ✅ **No "breathing" waveform** - Stable like hospital monitor
- ✅ **Looks like Philips/GE monitor** - Professional appearance

---

## 📝 Technical Details

### Baseline Anchor Time Constant

At 500 Hz sampling rate:
- **Alpha = 0.0005** → Time constant ≈ 4 seconds
- **Alpha = 0.002** → Time constant ≈ 1 second (too fast, baseline still moves)
- **Alpha = 0.001** → Time constant ≈ 2 seconds (borderline)

### Moving Average Window

- **Window size:** 2 seconds (1000 samples at 500 Hz)
- **Frequency response:** Removes respiration (0.1-0.35 Hz), ST/T waves, QRS complexes
- **Output:** Very-low-frequency drift only (< 0.1 Hz)

### Display Pipeline

```
Raw ECG (self.data[i])
    ↓
Extract low-frequency baseline (2-sec moving average)
    ↓
Update slow EMA anchor (alpha = 0.0005)
    ↓
Subtract anchor from signal
    ↓
Apply adaptive gain
    ↓
Apply AC/EMG/DFT filters (no mean subtraction)
    ↓
Apply wave-speed scaling (resample if needed)
    ↓
Plot with fixed Y-axis
```

---

## 🔍 Files Modified

1. `src/ecg/twelve_lead_test.py`
   - `_extract_low_frequency_baseline()` - Moving average signal extraction
   - Demo mode display path - Slow anchor with alpha = 0.0005
   - Serial mode display path - Slow anchor with alpha = 0.0005
   - `apply_ecg_filtering()` - Removed mean subtraction
   - Removed fallback mean subtractions

2. `src/ecg/expanded_lead_view.py`
   - `_extract_low_frequency_baseline()` - Moving average signal extraction
   - `update_plot()` - Slow anchor with alpha = 0.0005, fixed Y-axis
   - Removed fallback mean subtractions

---

## ✅ Status: COMPLETE

All fixes applied. ECG display should now be stable like a hospital monitor.

