# Clinical Measurement Validation Notes

## Reference Values (GE/Philips Standard)
- **HR**: 100 bpm
- **RR**: 600 ms
- **PR**: 168 ms
- **QRS**: 87 ms
- **QT/QTc**: 315/407 ms (QTc = Bazett)
- **P/QRS/T Axes**: 47/33/46 degrees
- **RV5/SV1**: 0.972/-0.485 mV
- **RV5+SV1**: 0.486 mV (algebraic sum)
- **QTcF**: 0.525 s = 525 ms ⚠️ **DISCREPANCY**

## QTcF Discrepancy Analysis

**Expected Fridericia Calculation:**
- QT = 315 ms = 0.315 s
- RR = 600 ms = 0.6 s
- QTcF = QT / RR^(1/3) = 0.315 / (0.6^(1/3)) = 0.315 / 0.843 ≈ **374 ms**

**Reference Software Shows:** 525 ms

**Possible Explanations:**
1. Reference software uses a different correction formula (not Fridericia)
2. Different RR value used in reference calculation
3. Typo in reference value
4. Reference software uses Hodges/Framingham or other correction

**Current Implementation:**
- ✅ Uses correct Fridericia formula: `QTcF = QT / RR^(1/3)`
- ✅ Calculated in seconds, converted to ms
- ✅ Displayed in ms only (no seconds)

## Measurement Alignment Strategy

### 1. PR Interval (Target: 168 ms ±5-10 ms)
- **Current Method**: P-wave onset detection using derivative threshold
- **Window**: 40-250 ms before R-peak
- **Averaging**: Median of 5 beats
- **Action**: Verify detection thresholds match GE/Philips fiducial placement

### 2. QRS Duration (Target: 87 ms ±5-10 ms)
- **Current Method**: Q-onset to S-offset using derivative-based detection
- **Window**: ±120 ms around R-peak (scaled by sampling rate)
- **Averaging**: Mean of 5 beats
- **Action**: Verify Q/S detection thresholds match GE/Philips

### 3. QT Interval (Target: 315 ms ±5-10 ms)
- **Current Method**: Q-onset to T-end (return to baseline)
- **Q Detection**: Min within 40 ms before R
- **T-end Detection**: Return to baseline within 500 ms after R
- **Averaging**: Mean of 5 beats
- **Action**: Verify T-end detection threshold (currently 0.15 × std)

### 4. QTc Bazett (Target: 407 ms ±5-10 ms)
- **Formula**: QTc = QT / √RR
- **Current Implementation**: ✅ Correct
- **Verification**: 315 / √0.6 = 315 / 0.775 = 406.5 ms ≈ 407 ms ✓

### 5. P/QRS/T Axes (Target: 47/33/46 degrees ±5-10°)
- **Current Method**: Net amplitude (max - min) in Lead I and aVF
- **QRS Window**: 100 ms around R-peak
- **P Window**: 80 ms around P-peak
- **T Window**: 120 ms around T-peak
- **Action**: Verify net amplitude calculation matches GE/Philips

### 6. RV5/SV1 (Target: 0.972/-0.485 mV ±0.01-0.02 mV)
- **Current Method**: 
  - TP baseline: Median of 150-350 ms before R-peak
  - QRS window: ±80 ms around R-peak
  - ADC→mV conversion: V5 = 1517.2 ADC/mV, V1 = 1100 ADC/mV
- **Action**: Verify TP baseline window and ADC calibration factors

## Implementation Status

✅ **Correctly Implemented:**
- RR calculation (60000 / HR)
- Bazett QTc formula
- Fridericia QTcF formula
- TP baseline detection
- RV5/SV1 sign preservation
- RV5+SV1 algebraic sum
- Raw signal isolation (no display filters affect measurements)

⚠️ **Needs Verification:**
- PR detection thresholds (may need fine-tuning)
- QRS Q/S detection thresholds (may need fine-tuning)
- QT T-end detection threshold (may need fine-tuning)
- Axis net amplitude calculation (verify window sizes)
- ADC calibration factors (verify against hardware)

## Next Steps

1. **Test with known ECG signal** matching reference values
2. **Compare fiducial placement** (P-onset, Q-onset, S-offset, T-end) with GE/Philips
3. **Fine-tune detection thresholds** to match reference machine
4. **Verify ADC calibration** factors match hardware specifications
5. **Investigate QTcF discrepancy** - determine if reference uses different formula

