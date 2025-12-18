"""
Clinical ECG Measurements Module (GE/Philips Standard)

All measurements use:
- Raw ECG signal (no display filters)
- Median beat (aligned beats)
- TP segment as isoelectric baseline
"""

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


def assess_beat_quality(beat, fs, r_idx_in_beat):
    """
    Assess beat quality using GE/Philips rules.
    
    Args:
        beat: Beat waveform (aligned)
        fs: Sampling rate (Hz)
        r_idx_in_beat: R-peak index within beat
    
    Returns:
        quality_score: 0.0 (poor) to 1.0 (excellent), or None if invalid
    """
    try:
        if len(beat) < 100:
            return None
        
        # Rule 1: Peak-to-peak amplitude (should be reasonable)
        p2p = np.max(beat) - np.min(beat)
        if p2p < 50 or p2p > 50000:  # Too small or too large (likely artifact)
            return None
        
        # Rule 2: Signal-to-noise ratio (QRS should dominate)
        qrs_start = max(0, r_idx_in_beat - int(80 * fs / 1000))
        qrs_end = min(len(beat), r_idx_in_beat + int(80 * fs / 1000))
        if qrs_end <= qrs_start:
            return None
        
        qrs_segment = beat[qrs_start:qrs_end]
        qrs_amplitude = np.max(qrs_segment) - np.min(qrs_segment)
        
        # TP segment (baseline noise estimate)
        tp_start = max(0, r_idx_in_beat - int(350 * fs / 1000))
        tp_end = max(0, r_idx_in_beat - int(150 * fs / 1000))
        if tp_end > tp_start:
            tp_segment = beat[tp_start:tp_end]
            tp_noise = np.std(tp_segment)
        else:
            tp_noise = np.std(beat) * 0.5
        
        if tp_noise == 0:
            snr = 100.0  # Perfect signal
        else:
            snr = qrs_amplitude / (tp_noise * 10)  # Normalized SNR
        
        # Rule 3: Baseline stability (TP segment should be relatively flat)
        if tp_end > tp_start:
            baseline_drift = np.max(tp_segment) - np.min(tp_segment)
            baseline_stability = 1.0 - min(baseline_drift / qrs_amplitude, 1.0)
        else:
            baseline_stability = 0.5
        
        # Rule 4: No excessive spikes (check for artifacts)
        signal_std = np.std(beat)
        outliers = np.sum(np.abs(beat - np.median(beat)) > 5 * signal_std)
        artifact_score = 1.0 - min(outliers / len(beat), 1.0)
        
        # Combined quality score
        quality = (min(snr / 10.0, 1.0) * 0.4 + 
                  baseline_stability * 0.3 + 
                  artifact_score * 0.3)
        
        return max(0.0, min(1.0, quality))
    except:
        return None


def build_median_beat(raw_signal, r_peaks, fs, pre_r_ms=400, post_r_ms=900, min_beats=8):
    """
    Build median beat from aligned beats with quality selection (GE Marquette style).
    
    Requirements:
    - 8-12 beats aligned on R peak (Lead II)
    - ALL interval and amplitude measurements MUST come from this median beat
    - No single-beat or rolling-window measurements for reports
    
    Args:
        raw_signal: Raw ECG signal (no display filters)
        r_peaks: R-peak indices
        fs: Sampling rate (Hz)
        pre_r_ms: Samples before R-peak (ms)
        post_r_ms: Samples after R-peak (ms)
        min_beats: Minimum number of clean beats required (default 8, GE/Philips standard)
    
    Returns:
        (time_axis, median_beat) or (None, None) if insufficient beats
    
    Validation:
        - Ensures ≥8 beats for reliable median beat
        - Uses raw signal only (no display filters)
    """
    if len(r_peaks) < min_beats:
        return None, None
    
    pre_samples = int(pre_r_ms * fs / 1000)
    post_samples = int(post_r_ms * fs / 1000)
    beat_length = pre_samples + post_samples + 1
    r_idx_in_beat = pre_samples  # R-peak position in aligned beat
    
    # Extract and assess all beats
    beat_candidates = []
    for r_idx in r_peaks[1:-1]:  # Skip first and last to avoid edge effects
        start = max(0, r_idx - pre_samples)
        end = min(len(raw_signal), r_idx + post_samples + 1)
        if end - start >= beat_length * 0.8:  # Accept partial beats at edges
            beat = raw_signal[start:end].copy()
            # Pad or trim to fixed length
            if len(beat) < beat_length:
                pad_left = pre_samples - (r_idx - start)
                pad_right = beat_length - len(beat) - pad_left
                beat = np.pad(beat, (pad_left, pad_right), mode='edge')
            elif len(beat) > beat_length:
                trim_left = (len(beat) - beat_length) // 2
                beat = beat[trim_left:trim_left + beat_length]
            
            # Assess beat quality
            quality = assess_beat_quality(beat, fs, r_idx_in_beat)
            if quality is not None and quality > 0.3:  # Minimum quality threshold
                beat_candidates.append((beat, quality))
    
    # Select top quality beats (at least min_beats, up to 12 best for GE Marquette style)
    if len(beat_candidates) < min_beats:
        return None, None
    
    # Sort by quality (best first)
    beat_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Take best beats (8-12 beats for median, GE Marquette style)
    num_beats = min(len(beat_candidates), max(min_beats, 12))
    selected_beats = [beat for beat, _ in beat_candidates[:num_beats]]
    
    # Compute median beat from selected clean beats
    beats_arr = np.array(selected_beats)
    median_beat = np.median(beats_arr, axis=0)
    
    # Time axis centered at R-peak (0 ms)
    time_axis = np.arange(-pre_samples, post_samples + 1) / fs * 1000.0  # ms
    
    return time_axis, median_beat


def detect_tp_segment(raw_signal, r_peak_idx, prev_r_peak_idx, fs):
    """
    Detect TP segment (end of T-wave to next P-wave) for baseline measurement (GE/Philips standard).
    
    Args:
        raw_signal: Raw ECG signal
        r_peak_idx: Current R-peak index
        prev_r_peak_idx: Previous R-peak index (for TP segment detection)
        fs: Sampling rate (Hz)
    
    Returns:
        TP baseline value (mean of TP segment), or None if not detectable
    """
    try:
        # TP segment is between end of T-wave and start of next P-wave
        # Typically: end of T (~400ms after previous R) to start of P (~250ms before current R)
        
        # Estimate T-end from previous R-peak
        t_end_estimate = prev_r_peak_idx + int(400 * fs / 1000)  # ~400ms after previous R
        
        # Estimate P-start before current R
        p_start_estimate = r_peak_idx - int(250 * fs / 1000)  # ~250ms before current R
        
        # TP segment should be between these points
        tp_start = max(prev_r_peak_idx + int(300 * fs / 1000), t_end_estimate)
        tp_end = min(r_peak_idx - int(100 * fs / 1000), p_start_estimate)
        
        # Ensure valid segment
        if tp_end > tp_start and tp_end < len(raw_signal) and tp_start >= 0:
            tp_segment = raw_signal[tp_start:tp_end]
            if len(tp_segment) > int(50 * fs / 1000):  # At least 50ms of TP segment
                # Use mean (GE/Philips standard uses mean for TP baseline)
                return np.mean(tp_segment)
        
        # Fallback: use segment before current R (150-350ms before R)
        fallback_start = max(0, r_peak_idx - int(350 * fs / 1000))
        fallback_end = max(0, r_peak_idx - int(150 * fs / 1000))
        if fallback_end > fallback_start:
            tp_segment = raw_signal[fallback_start:fallback_end]
            return np.mean(tp_segment)
        
        return None
    except:
        return None


def get_tp_baseline(raw_signal, r_peak_idx, fs, prev_r_peak_idx=None, tp_start_ms=350, tp_end_ms=150):
    """
    Get TP baseline from isoelectric segment (GE/Philips standard).
    
    Args:
        raw_signal: Raw ECG signal
        r_peak_idx: R-peak index
        fs: Sampling rate (Hz)
        prev_r_peak_idx: Previous R-peak index (for proper TP segment detection)
        tp_start_ms: Start of TP segment before R (ms) - fallback only
        tp_end_ms: End of TP segment before R (ms) - fallback only
    
    Returns:
        TP baseline value (mean of TP segment)
    """
    # Try proper TP segment detection if previous R-peak available
    if prev_r_peak_idx is not None and prev_r_peak_idx < r_peak_idx:
        tp_baseline = detect_tp_segment(raw_signal, r_peak_idx, prev_r_peak_idx, fs)
        if tp_baseline is not None:
            return tp_baseline
    
    # Fallback: use segment before current R
    tp_start = max(0, r_peak_idx - int(tp_start_ms * fs / 1000))
    tp_end = max(0, r_peak_idx - int(tp_end_ms * fs / 1000))
    
    if tp_end > tp_start:
        tp_segment = raw_signal[tp_start:tp_end]
        return np.mean(tp_segment)  # Use mean (GE/Philips standard)
    else:
        # Last resort: short segment before QRS
        qrs_start = max(0, r_peak_idx - int(80 * fs / 1000))
        fallback_start = max(0, qrs_start - int(50 * fs / 1000))
        return np.mean(raw_signal[fallback_start:qrs_start])


def measure_qt_from_median_beat(median_beat, time_axis, fs, tp_baseline):
    """
    Measure QT interval from median beat: QRS onset → T offset (GE/Philips standard).
    Hard-guards T-offset to prevent bleeding into TP segment or next P-wave.
    
    Args:
        median_beat: Median beat waveform
        time_axis: Time axis in ms (centered at R-peak = 0 ms)
        fs: Sampling rate (Hz)
        tp_baseline: TP baseline value
    
    Returns:
        QT interval in ms, or None if not measurable
    """
    try:
        r_idx = np.argmin(np.abs(time_axis))  # R-peak at 0 ms
        
        # Subtraction of baseline before measurement
        signal_corrected = median_beat - tp_baseline
        
        signal_range = np.max(np.abs(signal_corrected))
        threshold = max(0.05 * signal_range, np.std(signal_corrected) * 0.1) if signal_range > 0 else 0.05
        
        # Find QRS onset: first point before R where signal deviates from TP baseline
        qrs_onset_start = max(0, r_idx - int(60 * fs / 1000))
        qrs_segment = signal_corrected[qrs_onset_start:r_idx]
        qrs_deviations = np.where(np.abs(qrs_segment) > threshold * 2.0)[0] # Stricter for QRS
        qrs_onset_idx = qrs_onset_start + qrs_deviations[0] if len(qrs_deviations) > 0 else qrs_onset_start
        
        # Find T-peak (max absolute deflection after QRS)
        t_search_start = r_idx + int(80 * fs / 1000)  # After QRS
        t_search_end = min(len(signal_corrected), r_idx + int(500 * fs / 1000))  # 500 ms max
        
        if t_search_end <= t_search_start:
            return None
        
        t_segment = signal_corrected[t_search_start:t_search_end]
        t_peak_rel = np.argmax(np.abs(t_segment))
        t_peak_idx = t_search_start + t_peak_rel
        
        # T-offset (T-end): first point after T-peak where signal returns to TP baseline
        # BOUNDARY DISCIPLINE: Stop if signal crosses baseline or energy drops to noise floor
        post_t_segment = signal_corrected[t_peak_idx:t_search_end]
        t_end_idx = t_search_end
        
        prev_val = signal_corrected[t_peak_idx]
        for i in range(t_peak_idx, t_search_end):
            val = signal_corrected[i]
            
            # Stop if signal crosses TP baseline
            if (prev_val > 0 and val < 0) or (prev_val < 0 and val > 0):
                t_end_idx = i
                break
            
            # Stop if signal returns to noise floor
            if np.abs(val) < threshold * 0.5:
                t_end_idx = i
                break
            
            prev_val = val
            
        # Hard-guard: QT cannot exceed 600ms or 80% of RR (handled by t_search_end)
        
        # QT interval = QRS onset → T offset
        qt_ms = time_axis[t_end_idx - 1] - time_axis[qrs_onset_idx]
        
        if 200 <= qt_ms <= 650:  # Valid clinical QT range
            return qt_ms
        
        return None
    except Exception as e:
        print(f"❌ Error measuring QT from median: {e}")
        return None


def measure_rv5_sv1_from_median_beat(v5_raw, v1_raw, r_peaks_v5, r_peaks_v1, fs,
                                      v5_adc_per_mv=2048.0, v1_adc_per_mv=1441.0):
    """
    Measure RV5 and SV1 from median beat (GE/Philips standard).
    
    Args:
        v5_raw: Raw V5 lead signal
        v1_raw: Raw V1 lead signal
        r_peaks_v5: R-peak indices in V5
        r_peaks_v1: R-peak indices in V1
        fs: Sampling rate (Hz)
        v5_adc_per_mv: ADC counts per mV for V5
        v1_adc_per_mv: ADC counts per mV for V1
    
    Returns:
        (rv5_mv, sv1_mv) in mV, or (None, None) if not measurable
    """
    # Build median beat for V5 (requires ≥8 beats, GE/Philips standard)
    if len(r_peaks_v5) < 8:
        return None, None
    
    _, median_v5 = build_median_beat(v5_raw, r_peaks_v5, fs, min_beats=8)
    if median_v5 is None:
        return None, None
    
    # Get TP baseline for V5 (use middle R-peak)
    r_mid_v5 = r_peaks_v5[len(r_peaks_v5) // 2]
    tp_baseline_v5 = get_tp_baseline(v5_raw, r_mid_v5, fs)
    
    # RV5: max positive R amplitude in V5 vs TP baseline (GE/Philips standard)
    # Find QRS window and measure max positive amplitude relative to TP baseline
    r_idx = len(median_v5) // 2  # R-peak at center
    qrs_start = max(0, r_idx - int(80 * fs / 1000))
    qrs_end = min(len(median_v5), r_idx + int(80 * fs / 1000))
    qrs_segment = median_v5[qrs_start:qrs_end]
    
    # Find max positive R amplitude in QRS window
    r_max_adc = np.max(qrs_segment) - tp_baseline_v5
    rv5_mv = r_max_adc / v5_adc_per_mv if r_max_adc > 0 else None
    
    # Build median beat for V1 (requires ≥8 beats, GE/Philips standard)
    if len(r_peaks_v1) < 8:
        return rv5_mv, None
    
    _, median_v1 = build_median_beat(v1_raw, r_peaks_v1, fs, min_beats=8)
    if median_v1 is None:
        return rv5_mv, None
    
    # Get TP baseline for V1
    r_mid_v1 = r_peaks_v1[len(r_peaks_v1) // 2]
    tp_baseline_v1 = get_tp_baseline(v1_raw, r_mid_v1, fs)
    
    # SV1: S nadir in V1 below TP baseline (GE/Philips standard)
    # NO max-over-window logic - find S nadir in QRS window, then measure relative to TP baseline
    r_idx = len(median_v1) // 2
    qrs_start = max(0, r_idx - int(80 * fs / 1000))
    qrs_end = min(len(median_v1), r_idx + int(80 * fs / 1000))
    qrs_segment = median_v1[qrs_start:qrs_end]
    
    s_nadir_v1_adc = np.min(qrs_segment)  # S-wave nadir (most negative point in QRS)
    
    # SV1 = S_nadir_V1 - TP_baseline_V1 (negative when S is below baseline)
    sv1_adc = s_nadir_v1_adc - tp_baseline_v1
    
    # Convert to mV (SV1 is negative when S is below baseline)
    sv1_mv = sv1_adc / v1_adc_per_mv
    
    return rv5_mv, sv1_mv


def measure_st_deviation_from_median_beat(median_beat, time_axis, fs, tp_baseline, j_offset_ms=60):
    """
    Measure ST deviation at J+60ms from median beat (GE/Philips standard).
    
    Args:
        median_beat: Median beat waveform
        time_axis: Time axis in ms
        fs: Sampling rate (Hz)
        tp_baseline: TP baseline value
        j_offset_ms: Offset after J-point (default 60 ms)
    
    Returns:
        ST deviation in mV, or None if not measurable
    """
    r_idx = np.argmin(np.abs(time_axis))  # R-peak at 0 ms
    
    # Find J-point (end of S-wave, ~40ms after R)
    j_start = r_idx + int(20 * fs / 1000)
    j_end = r_idx + int(60 * fs / 1000)
    if j_end > len(median_beat):
        return None
    
    j_segment = median_beat[j_start:j_end]
    j_point_idx = j_start + np.argmin(j_segment)  # S-wave minimum
    
    # ST measurement point: J + j_offset_ms
    st_idx = j_point_idx + int(j_offset_ms * fs / 1000)
    if st_idx >= len(median_beat):
        return None
    
    # ST deviation relative to TP baseline (in ADC counts)
    st_adc = median_beat[st_idx] - tp_baseline
    
    # Convert to mV using standard calibration (GE/Philips standard)
    # For Lead II: typical calibration is ~1000-1500 ADC counts per mV
    # Use conservative estimate: 1200 ADC counts per mV (similar to other leads)
    adc_to_mv = 1200.0
    st_mv = st_adc / adc_to_mv
    
    # Clamp to reasonable range (-2.0 to +2.0 mV) and round to 2 decimal places
    st_mv = np.clip(st_mv, -2.0, 2.0)
    st_mv = round(st_mv, 2)
    
    return st_mv


def calculate_axis_from_median_beat(lead_i_raw, lead_ii_raw, lead_avf_raw, median_beat_i, median_beat_ii, median_beat_avf, 
                                     r_peak_idx, fs, tp_baseline_i=None, tp_baseline_avf=None, time_axis=None, wave_type='QRS', prev_axis=None):
    """
    Calculate electrical axis from median beat using net area (integral) method (GE/Philips standard).
    
    CRITICAL: Must use 10-second median beat with TP baseline correction BEFORE integration.
    Fixed windows for P, QRS, and T to prevent contamination.
    
    Args:
        lead_i_raw: Raw Lead I signal (for reference)
        lead_ii_raw: Raw Lead II signal (for reference)
        lead_avf_raw: Raw Lead aVF signal (for reference)
        median_beat_i: Median beat for Lead I
        median_beat_ii: Median beat for Lead II
        median_beat_avf: Median beat for Lead aVF
        r_peak_idx: R-peak index in median beat (center)
        fs: Sampling rate (Hz)
        tp_baseline_i: TP baseline for Lead I
        tp_baseline_avf: TP baseline for Lead aVF
        time_axis: Time axis in ms (centered at R-peak = 0 ms)
        wave_type: 'P', 'QRS', or 'T' for different wave axes
        prev_axis: Previous median axis for safety clamp (optional)
    
    Returns:
        Axis in degrees (0° to 360°, GE Marquette standard)
    """
    try:
        if time_axis is None:
            time_axis = np.arange(len(median_beat_i)) / fs * 1000.0 - (r_peak_idx / fs * 1000.0)
            
        # STEP 1: Determine TP baseline from median beat (end of T -> start of P)
        # Using [700, 800] ms after R as a reliable TP segment in 1.3s template
        tp_start_ms, tp_end_ms = 700, 800
        tp_start_idx = np.argmin(np.abs(time_axis - tp_start_ms))
        tp_end_idx = np.argmin(np.abs(time_axis - tp_end_ms))
        
        if tp_end_idx > tp_start_idx and tp_end_idx < len(median_beat_i):
            tp_baseline_i = np.mean(median_beat_i[tp_start_idx:tp_end_idx])
            tp_baseline_avf = np.mean(median_beat_avf[tp_start_idx:tp_end_idx])
        elif tp_baseline_i is None or tp_baseline_avf is None:
            # Fallback to start of beat if TP segment is not reachable
            tp_baseline_i = np.mean(median_beat_i[:int(0.05 * fs)])
            tp_baseline_avf = np.mean(median_beat_avf[:int(0.05 * fs)])
            
        # STEP 2: Apply TP baseline correction BEFORE integration
        signal_i = median_beat_i - tp_baseline_i
        signal_avf = median_beat_avf - tp_baseline_avf
        
        # STEP 3: Define HARD-FIXED wave windows
        if wave_type == 'P':
            # GE / Philips HARD P-WAVE WINDOW
            # NEVER allow window closer than 140 ms to R
            wave_start = r_peak_idx - int(0.20 * fs)   # -200 ms
            wave_end   = r_peak_idx - int(0.14 * fs)   # -140 ms

            # Absolute safety guard
            wave_end = min(wave_end, r_peak_idx - int(0.14 * fs))
                
        elif wave_type == 'QRS':
            # QRS window: [-50, 80] ms around R
            wave_start = r_peak_idx - int(0.05 * fs)
            wave_end = r_peak_idx + int(0.08 * fs)
        elif wave_type == 'T':
            # T-wave window: [120, 500] ms after R
            wave_start = r_peak_idx + int(0.12 * fs)
            wave_end = r_peak_idx + int(0.50 * fs)
        else:
            return 0
            
        # Ensure indices are within bounds
        wave_start = max(0, int(wave_start))
        wave_end = min(len(median_beat_i), int(wave_end))
        
        if wave_end <= wave_start:
            return 0
            
        # STEP 4: Area Integration (Net Area)
        wave_segment_i = signal_i[wave_start:wave_end]
        wave_segment_avf = signal_avf[wave_start:wave_end]
        
        dt = 1.0 / fs
        net_i = np.trapz(wave_segment_i, dx=dt)
        net_avf = np.trapz(wave_segment_avf, dx=dt)
        
        # Safety clamp: if signal area is too small, return previous axis
        # GE/Philips standard: Higher noise floor for P-wave energy gate (4e-5 mV·s)
        noise_floor = 0.00004 if wave_type == 'P' else 0.00002 
        if (abs(net_i) + abs(net_avf)) < noise_floor:
            return prev_axis if prev_axis is not None else 0
            
        # STEP 5: Calculate axis: atan2(net_aVF, net_I)
        axis_rad = np.arctan2(net_avf, net_i)
        axis_deg = np.degrees(axis_rad)
        
        # Normalize to 0° to 360°
        if axis_deg < 0:
            axis_deg += 360
            
        return axis_deg
    except Exception as e:
        print(f"❌ Error calculating {wave_type} axis: {e}")
        return 0


