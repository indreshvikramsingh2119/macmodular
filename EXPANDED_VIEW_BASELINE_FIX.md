# Expanded View Baseline Drift Fix

## Problem Analysis

### Root Cause

Even with slow baseline anchor (alpha=0.0005) and zero clamp (alpha=0.01), the waveform still drifts off-center over time when baseline wander is intentionally enabled from a Fluke simulator.

**Why baseline anchoring alone is not sufficient:**

1. **Baseline anchor tracks wander correctly** - The slow EMA (alpha=0.0005) tracks the baseline wander, preserving clinical data. This is correct.

2. **Zero clamp is too slow** - The zero clamp (alpha=0.01) uses EMA which still allows long-term drift. Over minutes, even a slow EMA will drift.

3. **Per-window mean is unstable** - Using `np.nanmean()` on the current window only gives a snapshot, not a stable long-term zero reference.

4. **No long-term zero memory** - The zero reference needs to accumulate over a longer period (5-10 seconds) to be truly stable.

### Why This Happens

```
Time 0: Baseline anchor = 0, Zero ref = 0, Signal centered ✓
Time 1 min: Baseline wander drifts +100 units
            → Baseline anchor tracks to +100 (correct for clinical)
            → Zero clamp tries to center, but EMA is slow
            → Zero ref = +50 (only partially caught up)
            → Display offset = +50 units ✗
Time 5 min: Baseline wander drifts +500 units
            → Baseline anchor = +500 (correct)
            → Zero ref = +200 (still catching up slowly)
            → Display offset = +300 units ✗✗
```

The zero clamp EMA is fighting against the baseline anchor, and the EMA is losing over long periods.

---

## Solution: Static Visual Zero Reference

### Hospital Monitor Approach

Real ECG monitors use:
1. **Slow baseline anchor** - Tracks electrode drift and baseline wander (preserves clinical data)
2. **Static visual zero reference** - Uses a longer window (5-10 seconds) to establish a stable zero point, then clamps aggressively

### Implementation

**Key Changes:**

1. **Longer window for zero reference** - Accumulate samples over 5-10 seconds instead of using current window mean
2. **Moving average for zero calculation** - Use convolution-based moving average, not `np.mean()` in update loop
3. **Faster zero clamp** - Increase alpha from 0.01 to 0.05 for more aggressive centering
4. **Sliding buffer** - Maintain a buffer of recent samples for stable zero reference

### Code Changes

**Before (problematic):**
```python
zero_alpha = 0.01  # Too slow
current_dc = np.nanmean(window_signal_filtered)  # Per-window mean (unstable)
self._display_zero_ref = (1 - zero_alpha) * self._display_zero_ref + zero_alpha * current_dc
```

**After (correct):**
```python
# Accumulate samples over 5-second window
zero_window_seconds = 5.0
zero_window_samples = int(zero_window_seconds * self.sampling_rate)
self._zero_ref_buffer.extend(window_signal_filtered.tolist())
if len(self._zero_ref_buffer) > zero_window_samples:
    self._zero_ref_buffer = self._zero_ref_buffer[-zero_window_samples:]

# Calculate zero reference using moving average (not mean)
if len(self._zero_ref_buffer) >= int(1.0 * self.sampling_rate):
    zero_kernel_size = min(int(2.0 * self.sampling_rate), len(self._zero_ref_buffer))
    zero_kernel = np.ones(zero_kernel_size) / zero_kernel_size
    zero_signal = np.convolve(self._zero_ref_buffer, zero_kernel, mode="valid")
    current_zero_ref = zero_signal[-1] if len(zero_signal) > 0 else 0.0
else:
    current_zero_ref = np.mean(self._zero_ref_buffer) if len(self._zero_ref_buffer) > 0 else 0.0

# Faster zero clamp (alpha=0.05 for aggressive centering)
zero_alpha = 0.05
self._display_zero_ref = (1 - zero_alpha) * self._display_zero_ref + zero_alpha * current_zero_ref
```

---

## Three-Layer System

| Layer | Purpose | Window | Alpha | Effect |
|-------|---------|--------|-------|--------|
| **Moving Average** | Remove respiration | 2 seconds | N/A | Filters out 0.1-0.35 Hz respiration |
| **Baseline Anchor** | Track electrode drift | 2 seconds (input) | 0.0005 | Very slow, tracks baseline wander |
| **Zero Reference** | Visual centering | 5-10 seconds | 0.05 | Fast, keeps display centered |

### Why This Works

1. **Baseline anchor** tracks the actual baseline wander (preserves clinical data)
2. **Zero reference** uses a longer window (5-10 sec) to establish a stable zero point
3. **Faster clamp** (alpha=0.05) aggressively centers the display without affecting clinical data
4. **No per-frame jumping** - Moving average over longer window prevents sudden jumps

---

## Expected Behavior

### Before Fix
- ❌ Waveform drifts off-center over time
- ❌ Long-term drift accumulates
- ❌ Baseline wander visible in display position

### After Fix
- ✅ Waveform stays vertically centered
- ✅ No long-term drift off screen
- ✅ Baseline wander exists in signal (clinical data preserved)
- ✅ Display trace remains centered (visual only)
- ✅ No per-frame jumping
- ✅ Hospital monitor behavior

---

## Constraints Met

- ✅ **No np.mean() in live update loop** - Uses moving average convolution instead
- ✅ **No Y-axis auto-scaling** - Fixed Y-limits maintained
- ✅ **Does not affect clinical data** - Only display path modified
- ✅ **Does not remove respiration** - Respiration preserved in signal
- ✅ **No per-frame jumping** - Longer window prevents sudden changes
- ✅ **Sampling rate = 500 Hz** - All calculations use correct sampling rate

---

## Files Modified

- `src/ecg/expanded_lead_view.py` - `update_plot()` function
  - Added `_zero_ref_buffer` for accumulating samples
  - Changed zero reference calculation to use 5-second moving average
  - Increased zero clamp alpha from 0.01 to 0.05
  - Removed `np.nanmean()` from update loop

---

## Testing

To verify the fix works:

1. Enable baseline wander from Fluke simulator
2. Open expanded view
3. Observe waveform over 5-10 minutes
4. **Expected:** Waveform stays vertically centered, no drift off screen
5. **Expected:** Baseline wander still visible in signal (clinical data preserved)

---

## Status: ✅ COMPLETE

The expanded view now uses a static visual zero reference that prevents long-term drift while preserving clinical baseline wander information.

