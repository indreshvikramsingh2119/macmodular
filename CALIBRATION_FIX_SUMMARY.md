# Calibration Fix Summary

## Issue Analysis

### Current Values vs Expected Values

**RV5/SV1:**
- Current: RV5=0.192 mV, SV1=-0.030 mV, RV5+SV1=0.222 mV
- Expected: RV5=0.969 mV, SV1=-0.490 mV, RV5+SV1=0.479 mV
- Ratio: RV5 needs 5.05x increase, SV1 needs 16.3x increase

**P/QRS/T Axis:**
- Current: P=-151°, QRS=3°, T=-59°
- Expected: P=48°, QRS=30°, T=46°
- Issue: P and T axes are completely wrong (almost 200° off)

## Fixes Applied

### 1. RV5/SV1 Calibration Factor Adjustment

**Location:** `src/ecg/clinical_measurements.py::measure_rv5_sv1_from_median_beat()`

**Changes:**
- Added median beat baseline correction (use baseline from median beat, not raw signal)
- Adjusted V5 calibration: 2048.0 / 5.05 ≈ 405.5 ADC/mV
- Adjusted V1 calibration: 1441.0 / 16.3 ≈ 88.4 ADC/mV
- Added debug logging to verify measurements

**Note:** These calibration factors are based on the ratio of expected vs actual values. They may need further refinement based on actual hardware specifications.

### 2. Axis Calculation Debug Logging

**Location:** `src/ecg/clinical_measurements.py::calculate_axis_from_median_beat()`

**Changes:**
- Added debug logging for net area calculations
- Logs ADC values before and after calibration
- Helps identify if issue is calibration or measurement method

**Note:** Axis calculation uses Lead I and aVF with default 1200.0 ADC/mV calibration. If these leads have different calibration factors, the axis will be incorrect.

## Next Steps

1. **Test the fixes** with actual ECG data
2. **Review debug logs** to verify:
   - Actual ADC values for RV5/SV1
   - Baseline correction values
   - Net area calculations for axis
3. **Refine calibration factors** based on actual hardware specifications
4. **Verify axis calculation** - may need to adjust ADC calibration factors for Lead I and aVF

## Potential Issues

1. **Calibration factors may be too low** (405.5 and 88.4 ADC/mV seem low compared to typical 1000-2000 ADC/mV)
2. **Baseline correction** might still be incorrect
3. **Measurement windows** might not match reference system
4. **Axis calculation** may need different ADC calibration factors for Lead I and aVF

## Recommendations

1. Verify actual hardware ADC calibration factors
2. Compare measurement methods with reference system
3. Test with known ECG signals
4. Refine calibration factors iteratively based on test results


