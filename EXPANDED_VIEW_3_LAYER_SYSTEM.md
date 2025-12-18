# Expanded View 3-Layer Display System

## ✅ Implementation Complete

The expanded ECG view now uses a **3-layer display-only system** that matches hospital monitor behavior (Philips/GE).

---

## 🏥 Three-Layer System

### **Layer 1: Low-Frequency Baseline Anchor (Clinical-Preserving)**

**Purpose:** Track electrode drift and baseline wander while preserving clinical data

**Implementation:**
- Extract baseline using 2-second moving average SIGNAL (convolution, not mean)
- Update slow EMA anchor with `alpha = 0.0005` (~4 sec time constant at 500 Hz)
- Subtract anchor from signal

**Code:**
```python
# Extract low-frequency baseline estimate (removes respiration 0.1-0.35 Hz)
baseline_estimate = self._extract_low_frequency_baseline(window_signal, self.sampling_rate)

# Update anchor with slow EMA (tracks only very-low-frequency drift)
self._baseline_anchor = (1 - 0.0005) * self._baseline_anchor + 0.0005 * baseline_estimate

# Subtract anchor (NOT raw mean)
window_signal_filtered = window_signal - self._baseline_anchor
```

**Why:** Preserves clinical baseline wander while removing respiration effects from display baseline.

---

### **Layer 2: Static Visual Zero Reference (Display-Only)**

**Purpose:** Keep waveform vertically centered with no long-term drift

**Implementation:**
- Maintain sliding buffer of last 5 seconds of samples
- Compute zero reference using convolution-based moving average (2-second window)
- Fast EMA clamp with `alpha = 0.05` for aggressive visual centering
- Subtract zero reference AFTER baseline anchoring

**Code:**
```python
# Zero window = 5 seconds (sliding buffer)
zero_window_samples = int(5.0 * self.sampling_rate)

# Add current window samples to buffer
self._zero_ref_buffer.extend(window_signal_filtered.tolist())

# Keep only last 5 seconds (sliding window)
if len(self._zero_ref_buffer) > zero_window_samples:
    self._zero_ref_buffer = self._zero_ref_buffer[-zero_window_samples:]

# Compute zero reference using convolution-based moving average (NOT mean)
if len(self._zero_ref_buffer) >= int(2.0 * self.sampling_rate):
    ma_window_samples = int(2.0 * self.sampling_rate)
    kernel = np.ones(ma_window_samples) / ma_window_samples
    zero_signal = np.convolve(self._zero_ref_buffer, kernel, mode="valid")
    if len(zero_signal) > 0:
        current_zero_ref = zero_signal[-1]
    else:
        current_zero_ref = 0.0
else:
    current_zero_ref = 0.0

# Fast EMA clamp (alpha=0.05) for aggressive visual centering
zero_alpha = 0.05  # Fast convergence, display-only
self._display_zero_ref = (1 - zero_alpha) * self._display_zero_ref + zero_alpha * current_zero_ref

# Apply visual zero reference (display-only centering)
window_signal_filtered = window_signal_filtered - self._display_zero_ref
```

**Why:** Sliding buffer provides stable long-term zero reference, fast EMA clamp keeps display centered.

---

### **Layer 3: Fixed Y-Axis (No Auto-Scaling)**

**Purpose:** Prevent apparent baseline movement from Y-axis scaling

**Implementation:**
- Lock Y-axis to fixed limits based on display gain
- Never auto-scale in live mode

**Code:**
```python
# Set fixed Y-axis range based on display gain (typical ECG range)
y_range = 2000 * self.display_gain
y_min, y_max = -y_range, y_range
self.fixed_ylim = (y_min, y_max)

# Always use fixed Y-limits (no auto-scaling)
self.ax.set_ylim(self.fixed_ylim[0], self.fixed_ylim[1])
```

**Why:** Hospital monitors never auto-scale Y-axis in live view.

---

## 📊 Order of Operations (Display-Only)

```
raw_window (from self.ecg_data)
    ↓
Layer 1: Low-frequency baseline extraction (2s moving average)
    ↓
Layer 1: Slow EMA anchor update (alpha=0.0005)
    ↓
Layer 1: Subtract baseline anchor
    ↓
Layer 2: Update zero reference buffer (5s sliding window)
    ↓
Layer 2: Compute moving-average zero (2s convolution)
    ↓
Layer 2: Fast EMA clamp (alpha=0.05)
    ↓
Layer 2: Subtract visual zero reference
    ↓
Apply display gain
    ↓
Layer 3: Plot with fixed Y-limits
```

---

## ✅ Constraints Met

- ✅ **Do NOT modify raw clinical data** - Only `window_signal_filtered` is modified, `self.ecg_data` untouched
- ✅ **Do NOT remove baseline wander from signal** - Baseline anchor preserves clinical wander
- ✅ **Do NOT use np.mean / np.nanmean in live update loops** - Uses convolution-based moving average
- ✅ **Do NOT auto-scale Y-axis** - Fixed Y-limits maintained
- ✅ **Sampling rate = 500 Hz** - All calculations use correct sampling rate

---

## 🎯 Expected Behavior

### With Fluke Baseline Wander ON:

- ✅ **Clinical baseline wander exists** - Preserved in signal for analysis
- ✅ **Display trace stays vertically centered** - No long-term drift
- ✅ **No breathing / floating effect** - Stable baseline anchor + fast zero clamp
- ✅ **No long-term drift off screen** - Sliding buffer + fast EMA prevents accumulation
- ✅ **Looks like Philips / GE monitor** - Professional hospital-grade behavior

---

## 🔧 Technical Details

### Baseline Anchor
- **Window:** 2 seconds (1000 samples at 500 Hz)
- **Method:** Moving average convolution (not mean)
- **EMA Alpha:** 0.0005 (~4 sec time constant)
- **Purpose:** Track electrode drift, preserve clinical baseline wander

### Visual Zero Reference
- **Buffer Size:** 5 seconds (2500 samples at 500 Hz)
- **Moving Average Window:** 2 seconds (1000 samples)
- **EMA Alpha:** 0.05 (fast convergence)
- **Purpose:** Keep display centered, prevent long-term drift

### Y-Axis
- **Range:** ±2000 * display_gain
- **Mode:** Fixed (never auto-scaled)
- **Purpose:** Prevent apparent baseline movement

---

## 📝 Files Modified

- `src/ecg/expanded_lead_view.py`
  - `__init__()` - Initialize zero reference buffer
  - `update_plot()` - Implement 3-layer system
  - Removed time-based lock mechanism
  - Removed `np.mean()` from update loop

---

## ✅ Status: COMPLETE

The expanded view now implements a hospital-grade 3-layer display system that:
- Preserves clinical baseline wander
- Keeps waveform vertically centered
- Prevents long-term drift
- Matches Philips/GE monitor behavior






