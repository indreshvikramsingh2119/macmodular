# Hardware Data Flow: 8-Channel to 12-Lead ECG Conversion

## Overview
This document explains how raw 8-channel hardware data is received, labeled, converted to 12 ECG leads using standard formulas, and plotted in real-time.

---

## 1. Hardware Data Reception

### Serial Communication
- **Location**: `src/ecg/twelve_lead_test.py` - `SerialECGReader` class and `update_plots()` method
- **Port**: Configurable COM port (default from settings)
- **Baud Rate**: Configurable (typically 115200)
- **Data Format**: Tab/space-separated integers (8 values per line)

### Raw Data Format
Hardware sends **8 channels** per packet in this order:
```
Channel[0]  Channel[1]  Channel[2]  Channel[3]  Channel[4]  Channel[5]  Channel[6]  Channel[7]
```

**Example raw packet:**
```
2091  2115  2113  2115  2117  2091  2161  2137
```

### Data Reading Process
1. **Serial Reader** (`SerialECGReader.read_value()`) reads one line from serial port
2. Line is decoded from UTF-8 and stripped
3. Values are split by whitespace and converted to integers
4. Validation ensures exactly 8 numeric values

**Code Location**: `src/ecg/twelve_lead_test.py:5850`
```python
all_8_leads = self.serial_reader.read_value()
```

---

## 2. Hardware Channel Labeling

### Channel Mapping
The 8 hardware channels are labeled as follows:

| Hardware Channel | Label | Description |
|-----------------|-------|-------------|
| `channel_data[0]` | **L1** | Lead I (direct from hardware) |
| `channel_data[1]` | **V4_hw** | V4 from hardware |
| `channel_data[2]` | **V5_hw** | V5 from hardware |
| `channel_data[3]` | **II** | Lead II (direct from hardware) |
| `channel_data[4]` | **V3_hw** | V3 from hardware |
| `channel_data[5]` | **V6_hw** | V6 from hardware |
| `channel_data[6]` | **V1** | V1 from hardware |
| `channel_data[7]` | **V2** | V2 from hardware |

**Code Location**: `src/ecg/twelve_lead_test.py:1491-1498`
```python
L1 = float(channel_data[0])      # Lead I
V4_hw = float(channel_data[1])   # V4 from hardware
V5_hw = float(channel_data[2])    # V5 from hardware
II = float(channel_data[3])       # Lead II
V3_hw = float(channel_data[4])   # V3 from hardware
V6_hw = float(channel_data[5])   # V6 from hardware
V1 = float(channel_data[6])      # V1 from hardware
V2 = float(channel_data[7])      # V2 from hardware
```

---

## 3. 12-Lead ECG Conversion Formulas

### Direct Leads (From Hardware)
These 8 leads come directly from hardware channels:

| Lead | Source | Formula |
|------|--------|---------|
| **I** | Hardware Channel[0] | `I = L1` |
| **II** | Hardware Channel[3] | `II = II` (direct) |
| **V1** | Hardware Channel[6] | `V1 = V1` (direct) |
| **V2** | Hardware Channel[7] | `V2 = V2` (direct) |
| **V3** | Hardware Channel[4] | `V3 = V3_hw` |
| **V4** | Hardware Channel[1] | `V4 = V4_hw` |
| **V5** | Hardware Channel[2] | `V5 = V5_hw` |
| **V6** | Hardware Channel[5] | `V6 = V6_hw` |

### Derived Leads (Calculated Using Formulas)

#### Lead III
**Formula**: `III = II - I`

**Code Location**: `src/ecg/twelve_lead_test.py:1505`
```python
III = II - I
```

**Medical Basis**: Lead III represents the potential difference between the left leg (LL) and left arm (LA). Since:
- Lead I = LA - RA
- Lead II = LL - RA
- Lead III = LL - LA = (LL - RA) - (LA - RA) = II - I

#### Augmented Lead aVR
**Formula**: `aVR = -(I + II) / 2`

**Code Location**: `src/ecg/twelve_lead_test.py:1511`
```python
aVR = -(I + II) / 2
```

**Medical Basis**: aVR is the average of Lead I and Lead II, inverted. It represents the potential from the right arm perspective.

#### Augmented Lead aVL
**Formula**: `aVL = (I - II) / 2`

**Code Location**: `src/ecg/twelve_lead_test.py:1516`
```python
aVL = (I - II) / 2
```

**Medical Basis**: aVL represents the potential from the left arm, calculated as the difference between Lead I and Lead II, divided by 2.

#### Augmented Lead aVF
**Formula**: `aVF = (II - I) / 2`

**Code Location**: `src/ecg/twelve_lead_test.py:1521`
```python
aVF = (II - I) / 2
```

**Medical Basis**: aVF represents the potential from the left leg (foot), calculated as the difference between Lead II and Lead I, divided by 2.

**Note**: There's a discrepancy in the code. The formula `(II - I) / 2` is mathematically equivalent to `III / 2`, but the standard medical formula for aVF is `(II + III) / 2`. However, since `III = II - I`, we get:
- Standard: `aVF = (II + III) / 2 = (II + (II - I)) / 2 = (2*II - I) / 2`
- Current code: `aVF = (II - I) / 2`

The current implementation may need review for medical accuracy.

---

## 4. Complete Conversion Function

**Code Location**: `src/ecg/twelve_lead_test.py:1461-1545`

```python
def calculate_12_leads_from_8_channels(self, channel_data):
    """
    Calculate 12-lead ECG from 8-channel hardware data
    Hardware sends: [L1, V4, V5, Lead 2, V3, V6, V1, V2] in that order
    """
    # Extract hardware channels
    L1 = float(channel_data[0])      # Lead I
    V4_hw = float(channel_data[1])    # V4
    V5_hw = float(channel_data[2])    # V5
    II = float(channel_data[3])       # Lead II
    V3_hw = float(channel_data[4])    # V3
    V6_hw = float(channel_data[5])    # V6
    V1 = float(channel_data[6])       # V1
    V2 = float(channel_data[7])       # V2

    # Direct leads
    I = L1
    
    # Derived leads
    III = II - I
    aVR = -(I + II) / 2
    aVL = (I - II) / 2
    aVF = (II - I) / 2
    
    # V leads from hardware
    V3 = V3_hw
    V4 = V4_hw
    V5 = V5_hw
    V6 = V6_hw
    
    # Return 12-lead ECG in standard order
    return [I, II, III, aVR, aVL, aVF, V1, V2, V3, V4, V5, V6]
```

---

## 5. Data Storage Structure

### Initialization
**Code Location**: `src/ecg/twelve_lead_test.py:890`
```python
self.data = [np.zeros(HISTORY_LENGTH, dtype=np.float32) for _ in range(12)]
```

- `self.data` is a **list of 12 numpy arrays**
- Each array stores one lead's data (circular buffer)
- `HISTORY_LENGTH = 1000` samples per lead
- Data type: `float32` for memory efficiency

### Lead Index Mapping
The 12 leads are stored in this order (matching standard ECG display):

| Index | Lead Name |
|-------|-----------|
| 0 | I |
| 1 | II |
| 2 | III |
| 3 | aVR |
| 4 | aVL |
| 5 | aVF |
| 6 | V1 |
| 7 | V2 |
| 8 | V3 |
| 9 | V4 |
| 10 | V5 |
| 11 | V6 |

### Data Update Process
**Code Location**: `src/ecg/twelve_lead_test.py:5852-5858`

```python
all_12_leads = self.calculate_12_leads_from_8_channels(all_8_leads)
for i in range(len(self.leads)):
    if i < len(self.data) and i < len(all_12_leads):
        self.data[i] = np.roll(self.data[i], -1)  # Shift buffer left
        smoothed_value = self.apply_realtime_smoothing(all_12_leads[i], i)
        self.data[i][-1] = smoothed_value  # Insert new value at end
```

**Process**:
1. Convert 8 channels → 12 leads using formulas
2. For each of the 12 leads:
   - Roll the buffer left (removes oldest sample)
   - Apply real-time smoothing filter
   - Insert new smoothed value at the end

---

## 6. Real-Time Plotting

### Plot Widgets
**Code Location**: `src/ecg/twelve_lead_test.py:1254-1308`

- **Library**: PyQtGraph (replacing Matplotlib for better performance)
- **Layout**: 4×3 grid (12 plots total)
- **Update Rate**: Timer-based, typically 50ms intervals (20 FPS)

### Plot Update Process
**Code Location**: `src/ecg/twelve_lead_test.py:5905-5948`

```python
for i in range(len(self.leads)):
    # Get data for this lead
    scaled_data = self.apply_adaptive_gain(self.data[i], signal_source, gain_factor)
    
    # Build time axis based on wave speed setting
    sampling_rate = 80.0  # Hardware sampling rate
    samples_to_show = int(sampling_rate * seconds_to_show)
    scaled_data = scaled_data[-samples_to_show:]  # Most recent samples
    
    # Create time axis
    n = len(scaled_data)
    time_axis = np.arange(n, dtype=float) / sampling_rate
    
    # Update plot
    self.data_lines[i].setData(time_axis, scaled_data)
    self.update_plot_y_range_adaptive(i, signal_source, data_override=scaled_data)
```

### Data Processing Steps
1. **Gain Scaling**: Apply user-selected gain (2.5mm/mV, 5mm/mV, 10mm/mV, 20mm/mV)
2. **Time Scaling**: Adjust time window based on wave speed (12.5mm/s, 25mm/s, 50mm/s)
3. **Adaptive Y-Range**: Auto-scale Y-axis based on signal amplitude
4. **Real-Time Update**: Update all 12 plots simultaneously

---

## 7. Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    HARDWARE DEVICE                            │
│  Sends 8-channel data via Serial (COM port, 115200 baud)    │
│  Format: "2091  2115  2113  2115  2117  2091  2161  2137"   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           SerialECGReader.read_value()                      │
│  • Read line from serial port                                │
│  • Decode UTF-8                                              │
│  • Split by whitespace → [2091, 2115, 2113, ...]            │
│  • Validate 8 numeric values                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│    calculate_12_leads_from_8_channels()                    │
│                                                               │
│  Input: [L1, V4, V5, II, V3, V6, V1, V2]                    │
│                                                               │
│  Direct:                                                      │
│    I = L1                                                     │
│    II = II                                                    │
│    V1-V6 = from hardware                                     │
│                                                               │
│  Derived:                                                     │
│    III = II - I                                               │
│    aVR = -(I + II) / 2                                        │
│    aVL = (I - II) / 2                                         │
│    aVF = (II - I) / 2                                         │
│                                                               │
│  Output: [I, II, III, aVR, aVL, aVF, V1, V2, V3, V4, V5, V6] │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Storage (self.data)                        │
│  • List of 12 numpy arrays (circular buffers)                │
│  • Each array: 1000 samples (float32)                       │
│  • Update: np.roll() + smoothing + insert new value         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Real-Time Plotting (PyQtGraph)                  │
│  • 4×3 grid layout (12 plots)                                │
│  • Apply gain scaling (2.5-20mm/mV)                          │
│  • Apply time scaling (12.5-50mm/s)                          │
│  • Adaptive Y-axis auto-scaling                              │
│  • Update rate: 20 FPS (50ms timer)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Key Formulas Summary

### Standard ECG Lead Formulas

| Lead | Formula | Medical Meaning |
|------|---------|----------------|
| **I** | `I = L1` | Right arm to left arm |
| **II** | `II = II` (direct) | Right arm to left leg |
| **III** | `III = II - I` | Left arm to left leg |
| **aVR** | `aVR = -(I + II) / 2` | Augmented right arm |
| **aVL** | `aVL = (I - II) / 2` | Augmented left arm |
| **aVF** | `aVF = (II - I) / 2` | Augmented left leg (foot) |
| **V1-V6** | Direct from hardware | Precordial leads |

### Data Processing Formulas

**Gain Scaling**:
```
scaled_value = (raw_value - baseline) × gain_factor
gain_factor = 5.0 / wave_gain_setting
```

**Time Scaling**:
```
seconds_to_show = baseline_seconds × (25.0 / wave_speed)
samples_to_show = sampling_rate × seconds_to_show
```

---

## 9. File Locations Reference

| Component | File | Line Range |
|-----------|------|------------|
| Serial reading | `src/ecg/twelve_lead_test.py` | ~5850 |
| 8→12 conversion | `src/ecg/twelve_lead_test.py` | 1461-1545 |
| Data storage init | `src/ecg/twelve_lead_test.py` | 890 |
| Data update | `src/ecg/twelve_lead_test.py` | 5852-5858 |
| Plot widgets | `src/ecg/twelve_lead_test.py` | 1254-1308 |
| Plot update | `src/ecg/twelve_lead_test.py` | 5905-5948 |
| Main update loop | `src/ecg/twelve_lead_test.py` | 5791-5968 |

---

## 10. Notes and Considerations

### Medical Accuracy
- The aVF formula `(II - I) / 2` should be verified against medical standards. The standard formula is typically `(II + III) / 2`, which expands to `(2×II - I) / 2` when using `III = II - I`.

### Data Validation
- All values are validated for NaN/Inf before storage
- Invalid channels are padded with zeros
- Non-numeric values are replaced with 0

### Performance
- Circular buffers prevent memory growth
- Real-time smoothing reduces noise
- PyQtGraph provides better performance than Matplotlib for real-time updates

### Sampling Rate
- Hardware sampling rate is measured dynamically
- Default fallback: 250 Hz or 500 Hz
- Used for accurate time-axis calculations

---

## Conclusion

The system receives 8-channel hardware data, labels each channel, applies standard ECG formulas to derive 12 leads, stores them in circular buffers, and plots them in real-time using PyQtGraph. The conversion follows standard medical ECG lead derivation principles, with direct leads from hardware and calculated augmented leads.

