# Baseline Wander & Respiration Instability - Code Audit

## 🔍 CRITICAL ISSUES FOUND

### **Issue #1: Per-Window Mean Subtraction in Display Loop (PRIMARY CAUSE)**
**Location:** `twelve_lead_test.py:6424` (Demo Mode) and `6592` (Serial Mode)

**Problem:**
```python
# Line 6424 (Demo Mode):
raw = raw - np.nanmean(raw)  # ❌ Re-centers ENTIRE buffer every frame

# Line 6592 (Serial Mode):
filtered_slice = filtered_slice - np.mean(filtered_slice)  # ❌ Re-centers window every frame
```

**Why This Causes Floating:**
- Every frame, the ENTIRE buffer (or window) is re-centered to zero mean
- As new data arrives, the mean changes → baseline jumps
- Respiration causes slow baseline drift → mean changes → waves float up/down
- Visual RR intervals appear to change because baseline is constantly shifting

**Impact:**
- Waves "float" up and down with respiration
- Baseline jumps every frame
- Visual BPM/RR appears unstable even though raw data is correct
- Hospital monitors DON'T do this - they use slow anchor baseline

---

### **Issue #2: Double Baseline Correction in Expanded View**
**Location:** `expanded_lead_view.py:1160` and `1167`

**Problem:**
```python
# Line 1160:
window_signal_filtered = window_signal - np.mean(window_signal)  # First centering

# Line 1167:
window_signal_filtered = window_signal_filtered - np.mean(window_signal_filtered)  # ❌ SECOND centering!
```

**Why This Causes Jumping:**
- Mean is subtracted twice
- Second subtraction on already-centered data creates instability
- Window slides → mean changes → double correction amplifies jumps

**Impact:**
- Expanded view waves jump more than 12-lead view
- Double correction amplifies respiration effects

---

### **Issue #3: Per-Window Median Centering in Demo Manager**
**Location:** `demo_manager.py:670-672`

**Problem:**
```python
# Line 670-672:
centered_slice = np.array(data_slice, dtype=float)
slice_center = np.nanmedian(centered_slice)
centered_slice = centered_slice - slice_center  # ❌ Re-centers every frame
```

**Why This Causes Instability:**
- Demo manager applies median centering to display slice
- This happens INSIDE the display update loop
- Combined with per-window mean subtraction in `update_plots()`, creates double correction

**Impact:**
- Demo mode has extra baseline instability
- Waves float more than hardware mode

---

### **Issue #4: Complex Baseline Filter in Expanded View Init**
**Location:** `expanded_lead_view.py:877-879`

**Problem:**
```python
# Line 877-879:
from ecg.ecg_filters import ecg_with_respiratory_baseline
ecg_filtered, _ = ecg_with_respiratory_baseline(self.ecg_data, self.sampling_rate)
```

**Why This Causes Issues:**
- Complex filter applied during initialization
- Then per-window mean subtraction applied again in `update_plot()` (line 1160)
- Double processing creates baseline instability

**Impact:**
- Initial view may look different from live updates
- Baseline behavior inconsistent between init and updates

---

### **Issue #5: Resampling Without Baseline Preservation**
**Location:** `twelve_lead_test.py:6445-6447`

**Problem:**
```python
# Line 6445-6447:
x_src = np.linspace(0.0, 1.0, src.size)
x_dst = np.linspace(0.0, 1.0, display_len)
resampled = np.interp(x_dst, x_src, src)  # ❌ Interpolation can amplify baseline drift
```

**Why This Causes Issues:**
- Linear interpolation on already-unstable baseline
- Resampling can amplify low-frequency baseline wander
- No baseline anchor before resampling

**Impact:**
- Baseline drift amplified by resampling
- Waves appear to "breathe" with respiration

---

### **Issue #6: Baseline Centering in apply_adaptive_gain()**
**Location:** `twelve_lead_test.py:4086, 4092`

**Problem:**
```python
# Line 4086 (human_body):
baseline = np.mean(device_data)
centered = (device_data - baseline) * gain_factor * 8

# Line 4092 (weak_body):
baseline = np.mean(device_data)
centered = (device_data - baseline) * gain_factor * 15
```

**Why This Causes Issues:**
- `apply_adaptive_gain()` is called in serial mode display path (line 6568)
- Applies mean subtraction BEFORE the per-window mean subtraction (line 6592)
- Double baseline correction amplifies instability

**Impact:**
- Extra baseline correction in serial mode
- Combined with line 6592, creates triple correction

---

### **Issue #7: DC Offset Removal in apply_ecg_filtering()**
**Location:** `twelve_lead_test.py:4249`

**Problem:**
```python
# Line 4249:
signal = signal - np.mean(signal)  # ❌ Removes DC offset
```

**Why This Causes Issues:**
- `apply_ecg_filtering()` is called in `update_ecg_lead()` (line 4207)
- This function applies mean subtraction
- If used in display path, adds another baseline correction layer

**Impact:**
- Additional baseline correction if filtering is applied during display
- May not be active in current code path (needs verification)

---

### **Issue #8: Real-time Smoothing During Acquisition**
**Location:** `twelve_lead_test.py:4316-4356` and `6471, 6506`

**Problem:**
```python
# Line 6471, 6506:
smoothed_value = self.apply_realtime_smoothing(value, i)
self.data[i][-1] = smoothed_value  # ❌ Stores smoothed value in raw buffer
```

**Why This Causes Issues:**
- Smoothing applied during acquisition
- Smoothed values stored in `self.data[i]`
- Clinical analysis uses smoothed data, not true raw data
- Display then applies additional processing

**Impact:**
- Clinical measurements use smoothed data (not ideal)
- Double smoothing (acquisition + display)

---

## 🔧 EXACT FIXES REQUIRED

### **Fix #1: Replace Per-Window Mean Subtraction with Slow Anchor Baseline**
**File:** `twelve_lead_test.py`

**REMOVE:**
- Line 6424: `raw = raw - np.nanmean(raw)` (Demo Mode)
- Line 6592: `filtered_slice = filtered_slice - np.mean(filtered_slice)` (Serial Mode)

**REPLACE WITH:**
Slow anchor baseline (2-4 second time constant):
```python
# Initialize anchor baseline (once per lead, outside update loop)
if not hasattr(self, '_baseline_anchors'):
    self._baseline_anchors = [0.0] * 12

# In update loop (per lead):
# Calculate slow-moving baseline anchor (2-4 sec time constant)
alpha = 0.01  # Smoothing factor (adjust for 2-4 sec time constant)
current_mean = np.nanmean(raw) if len(raw) > 0 else 0.0
self._baseline_anchors[i] = (1 - alpha) * self._baseline_anchors[i] + alpha * current_mean

# Subtract anchor (NOT current mean)
raw = raw - self._baseline_anchors[i]
```

**Why This Works:**
- Baseline anchor moves slowly (2-4 sec), not every frame
- Respiration effects are preserved but don't cause jumping
- Matches hospital monitor behavior

---

### **Fix #2: Remove Double Baseline Correction**
**File:** `expanded_lead_view.py`

**REMOVE:**
- Line 1167: `window_signal_filtered = window_signal_filtered - np.mean(window_signal_filtered)`

**KEEP:**
- Line 1160: `window_signal_filtered = window_signal - np.mean(window_signal)` (single correction)

**REPLACE WITH:**
Same slow anchor baseline as Fix #1

---

### **Fix #3: Remove Demo Manager Per-Window Centering**
**File:** `demo_manager.py`

**REMOVE:**
- Lines 670-672: Median centering in display loop

**MOVE TO:**
Apply slow anchor baseline in `update_plots()` instead (Fix #1 handles this)

---

### **Fix #4: Simplify Expanded View Init**
**File:** `expanded_lead_view.py`

**REMOVE:**
- Lines 877-879: Complex `ecg_with_respiratory_baseline` filter

**REPLACE WITH:**
Simple slow anchor baseline (same as Fix #1)

---

### **Fix #5: Apply Baseline Anchor Before Resampling**
**File:** `twelve_lead_test.py`

**MOVE:**
- Apply slow anchor baseline (Fix #1) BEFORE resampling (line 6445)
- This ensures stable baseline during interpolation

---

### **Fix #6: Remove Baseline Centering from apply_adaptive_gain()**
**File:** `twelve_lead_test.py`

**REMOVE:**
- Line 4086: `baseline = np.mean(device_data)` and `centered = (device_data - baseline)`
- Line 4092: `baseline = np.mean(device_data)` and `centered = (device_data - baseline)`

**REPLACE WITH:**
```python
# For human_body and weak_body:
# Don't subtract mean here - slow anchor baseline handles it
centered = device_data * gain_factor * 8  # (or * 15 for weak_body)
```

**Why:**
- Slow anchor baseline (Fix #1) handles baseline correction
- No need for mean subtraction here

---

### **Fix #7: Verify apply_ecg_filtering() Usage**
**File:** `twelve_lead_test.py`

**CHECK:**
- Verify if `apply_ecg_filtering()` is called in display path
- If yes, REMOVE line 4249: `signal = signal - np.mean(signal)`
- Let slow anchor baseline handle baseline correction

---

### **Fix #8: Separate Raw and Smoothed Data**
**File:** `twelve_lead_test.py`

**CHANGE:**
- Store RAW values in `self.data[i]` (line 6472, 6506)
- Apply smoothing only for display, not during acquisition

**BEFORE:**
```python
smoothed_value = self.apply_realtime_smoothing(value, i)
self.data[i][-1] = smoothed_value  # ❌ Stores smoothed
```

**AFTER:**
```python
# Store raw value
self.data[i][-1] = value  # ✅ Store raw
# Smoothing applied only in display path (if needed)
```

**Why:**
- Clinical analysis needs true raw data
- Smoothing should be display-only

---

## 📋 SUMMARY: What to REMOVE, MOVE, KEEP

### **COMPLETE FILE-BY-FILE BREAKDOWN:**

#### **File: `twelve_lead_test.py`**

**Line 6424 (Demo Mode Display):**
- ❌ REMOVE: `raw = raw - np.nanmean(raw)`
- ✅ REPLACE: Slow anchor baseline (Fix #1)

**Line 6592 (Serial Mode Display):**
- ❌ REMOVE: `filtered_slice = filtered_slice - np.mean(filtered_slice)`
- ✅ REPLACE: Slow anchor baseline (Fix #1)

**Line 4086, 4092 (`apply_adaptive_gain()`):**
- ❌ REMOVE: `baseline = np.mean(device_data)` and mean subtraction
- ✅ KEEP: Gain multiplication only

**Line 4249 (`apply_ecg_filtering()`):**
- ❌ REMOVE: `signal = signal - np.mean(signal)` (if used in display path)
- ✅ VERIFY: Check if this function is called in display path

**Line 6472, 6506 (Data Acquisition):**
- ❌ CHANGE: Store raw values, not smoothed
- ✅ BEFORE: `self.data[i][-1] = smoothed_value`
- ✅ AFTER: `self.data[i][-1] = value` (raw)

#### **File: `expanded_lead_view.py`**

**Line 1160 (Update Plot):**
- ❌ REMOVE: `window_signal_filtered = window_signal - np.mean(window_signal)`
- ✅ REPLACE: Slow anchor baseline (Fix #1)

**Line 1167 (Update Plot):**
- ❌ REMOVE: `window_signal_filtered = window_signal_filtered - np.mean(window_signal_filtered)`
- ✅ REMOVE: Double correction

**Line 879 (Initialization):**
- ❌ REMOVE: `ecg_with_respiratory_baseline()` complex filter
- ✅ REPLACE: Slow anchor baseline (Fix #1)

#### **File: `demo_manager.py`**

**Line 672 (Display Processing):**
- ❌ REMOVE: `centered_slice = centered_slice - slice_center`
- ✅ REPLACE: Slow anchor baseline (Fix #1)

---

## 📋 SUMMARY: What to REMOVE, MOVE, KEEP

### **REMOVE (Causes Instability):**
1. ✅ `raw = raw - np.nanmean(raw)` in `update_plots()` (line 6424, 6592)
2. ✅ `window_signal_filtered - np.mean(window_signal_filtered)` (line 1167)
3. ✅ `centered_slice = centered_slice - slice_center` in demo manager (line 672)
4. ✅ `ecg_with_respiratory_baseline()` in expanded view init (line 879)
5. ✅ `baseline = np.mean(device_data)` in `apply_adaptive_gain()` (line 4086, 4092)
6. ✅ `signal = signal - np.mean(signal)` in `apply_ecg_filtering()` (line 4249) - if used in display
7. ✅ `apply_realtime_smoothing()` storing smoothed values in `self.data[i]` (line 6472, 6506)

### **MOVE to Display-Only (Slow Anchor Baseline):**
1. ✅ Replace per-window mean with slow anchor baseline (2-4 sec time constant)
2. ✅ Apply anchor BEFORE resampling
3. ✅ Use same anchor logic in demo, serial, and expanded views

### **KEEP Raw (Clinical Analysis):**
1. ✅ `self.data[i]` - Raw buffer (never modified)
2. ✅ `calculate_heart_rate(self.data[1])` - Uses raw data
3. ✅ `calculate_ecg_metrics()` - Uses raw data
4. ✅ All clinical calculations - Use raw data

---

## 🎯 UX-Safe Display Baseline Strategy

### **Hospital Monitor Behavior:**
- Baseline moves slowly (2-4 second time constant)
- NOT re-centered every window
- Respiration visible but doesn't cause jumping
- Waves appear stable while still showing breathing

### **Implementation:**
```python
# Per-lead slow anchor baseline (initialize once)
self._baseline_anchors = [0.0] * 12  # One per lead
self._baseline_alpha = 0.01  # ~3 sec time constant at 500 Hz

# In update loop (per lead):
current_mean = np.nanmean(display_window)
# Update anchor slowly
self._baseline_anchors[i] = (1 - self._baseline_alpha) * self._baseline_anchors[i] + self._baseline_alpha * current_mean
# Subtract anchor (NOT current mean)
display_signal = raw_signal - self._baseline_anchors[i]
```

**Benefits:**
- ✅ Stable baseline (no jumping)
- ✅ Respiration still visible (slow movement)
- ✅ Matches hospital monitor UX
- ✅ No impact on clinical measurements

---

## 🔍 VERIFICATION CHECKLIST

After fixes:
- [ ] No `np.mean()` or `np.nanmean()` in display update loops
- [ ] Slow anchor baseline used instead of per-window centering
- [ ] Single baseline correction per display path
- [ ] Baseline anchor applied before resampling
- [ ] `self.data[i]` remains raw (never modified)
- [ ] Clinical calculations unchanged

---

## 📊 EXPECTED RESULT

**Before:**
- Waves float up/down with respiration
- Baseline jumps every frame
- Visual RR appears unstable

**After:**
- Waves stable (baseline moves slowly)
- Respiration visible but smooth
- Visual RR matches clinical RR
- Hospital monitor-like UX

---

## 💻 IMPLEMENTATION: Slow Anchor Baseline

### **Step 1: Initialize Anchor Baselines (in `__init__` or first update)**

```python
# In ECGTestPage.__init__() or first update_plots() call:
if not hasattr(self, '_baseline_anchors'):
    self._baseline_anchors = [0.0] * 12  # One anchor per lead
    self._baseline_alpha = 0.01  # Smoothing factor (~3 sec time constant at 500 Hz)
    # Adjust alpha for different time constants:
    # alpha = 0.005 → ~6 sec time constant
    # alpha = 0.01  → ~3 sec time constant (recommended)
    # alpha = 0.02  → ~1.5 sec time constant
```

### **Step 2: Update Anchor in Display Loop**

**For Demo Mode (replace line 6424):**
```python
# Calculate slow-moving baseline anchor
if len(raw) > 0:
    current_mean = np.nanmean(raw)
    # Update anchor slowly (exponential moving average)
    self._baseline_anchors[i] = (1 - self._baseline_alpha) * self._baseline_anchors[i] + self._baseline_alpha * current_mean
    # Subtract anchor (NOT current mean)
    raw = raw - self._baseline_anchors[i]
else:
    raw = raw  # No change if no data
```

**For Serial Mode (replace line 6592):**
```python
# Calculate slow-moving baseline anchor
if len(filtered_slice) > 0:
    current_mean = np.mean(filtered_slice)
    # Update anchor slowly
    self._baseline_anchors[i] = (1 - self._baseline_alpha) * self._baseline_anchors[i] + self._baseline_alpha * current_mean
    # Subtract anchor (NOT current mean)
    filtered_slice = filtered_slice - self._baseline_anchors[i]
```

**For Expanded View (replace line 1160):**
```python
# Initialize anchor if needed
if not hasattr(self, '_baseline_anchor'):
    self._baseline_anchor = 0.0
    self._baseline_alpha = 0.01

# Calculate slow-moving baseline anchor
if len(window_signal) > 0:
    current_mean = np.mean(window_signal)
    # Update anchor slowly
    self._baseline_anchor = (1 - self._baseline_alpha) * self._baseline_anchor + self._baseline_alpha * current_mean
    # Subtract anchor (NOT current mean)
    window_signal_filtered = window_signal - self._baseline_anchor
else:
    window_signal_filtered = window_signal
```

### **Step 3: Remove All Other Baseline Corrections**

- Remove line 1167 (double correction in expanded view)
- Remove line 672 (demo manager median centering)
- Remove line 879 (complex filter in expanded init)
- Remove line 4086, 4092 (mean subtraction in apply_adaptive_gain)
- Remove line 4249 (if apply_ecg_filtering used in display)

### **Step 4: Verify Clinical Data Unchanged**

- Ensure `self.data[i]` stores raw values (not smoothed)
- Ensure `calculate_heart_rate()` uses `self.data[1]` (raw)
- Ensure `calculate_ecg_metrics()` uses `self.data[1]` (raw)

---

## ✅ FINAL CHECKLIST

After implementing fixes:

- [ ] No `np.mean()` or `np.nanmean()` in display update loops
- [ ] Slow anchor baseline initialized (12 anchors, one per lead)
- [ ] Anchor updated with exponential moving average
- [ ] Anchor subtracted (not current mean)
- [ ] All per-window mean subtractions removed
- [ ] Double baseline corrections removed
- [ ] `self.data[i]` stores raw values (not smoothed)
- [ ] Clinical calculations use raw data
- [ ] Display uses slow anchor baseline
- [ ] Baseline moves slowly (2-4 sec time constant)
- [ ] Respiration visible but doesn't cause jumping

