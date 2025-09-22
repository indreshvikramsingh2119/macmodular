#!/usr/bin/env python3
"""
Test script for the expanded lead view functionality
"""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
from ecg.expanded_lead_view import show_expanded_lead_view

def create_sample_ecg_data(duration=4, sampling_rate=500, heart_rate=72):
    """Create sample ECG data for testing"""
    t = np.linspace(0, duration, int(duration * sampling_rate))
    
    # Create a more realistic ECG waveform
    ecg = np.zeros_like(t)
    
    # Add multiple heartbeats
    rr_interval = 60.0 / heart_rate  # RR interval in seconds
    num_beats = int(duration / rr_interval)
    
    for i in range(num_beats):
        beat_start = i * rr_interval
        
        # P wave (atrial depolarization)
        p_start = beat_start + 0.1
        p_duration = 0.08
        p_mask = (t >= p_start) & (t <= p_start + p_duration)
        ecg[p_mask] += 0.1 * np.sin(2 * np.pi * (t[p_mask] - p_start) / p_duration)
        
        # QRS complex (ventricular depolarization)
        qrs_start = beat_start + 0.2
        qrs_duration = 0.1
        qrs_mask = (t >= qrs_start) & (t <= qrs_start + qrs_duration)
        
        # Q wave (negative)
        q_duration = 0.02
        q_mask = (t >= qrs_start) & (t <= qrs_start + q_duration)
        ecg[q_mask] -= 0.3 * np.sin(2 * np.pi * (t[q_mask] - qrs_start) / q_duration)
        
        # R wave (positive)
        r_start = qrs_start + q_duration
        r_duration = 0.04
        r_mask = (t >= r_start) & (t <= r_start + r_duration)
        ecg[r_mask] += 0.8 * np.sin(2 * np.pi * (t[r_mask] - r_start) / r_duration)
        
        # S wave (negative)
        s_start = r_start + r_duration
        s_duration = 0.02
        s_mask = (t >= s_start) & (t <= s_start + s_duration)
        ecg[s_mask] -= 0.2 * np.sin(2 * np.pi * (t[s_mask] - s_start) / s_duration)
        
        # T wave (ventricular repolarization)
        t_start = beat_start + 0.4
        t_duration = 0.16
        t_mask = (t >= t_start) & (t <= t_start + t_duration)
        ecg[t_mask] += 0.2 * np.sin(2 * np.pi * (t[t_mask] - t_start) / t_duration)
    
    # Add some noise
    noise = 0.02 * np.random.randn(len(t))
    ecg += noise
    
    return ecg

def main():
    """Main test function"""
    app = QApplication(sys.argv)
    
    # Create sample ECG data for different leads
    leads_data = {
        "I": create_sample_ecg_data(4, 500, 75),
        "II": create_sample_ecg_data(4, 500, 72),
        "III": create_sample_ecg_data(4, 500, 78),
        "aVR": create_sample_ecg_data(4, 500, 70),
        "aVL": create_sample_ecg_data(4, 500, 76),
        "aVF": create_sample_ecg_data(4, 500, 74),
        "V1": create_sample_ecg_data(4, 500, 73),
        "V2": create_sample_ecg_data(4, 500, 71),
        "V3": create_sample_ecg_data(4, 500, 77),
        "V4": create_sample_ecg_data(4, 500, 75),
        "V5": create_sample_ecg_data(4, 500, 72),
        "V6": create_sample_ecg_data(4, 500, 74)
    }
    
    print("Testing Expanded Lead View...")
    print("Available leads:", list(leads_data.keys()))
    
    # Test with Lead II
    test_lead = "II"
    print(f"Showing expanded view for Lead {test_lead}")
    
    show_expanded_lead_view(test_lead, leads_data[test_lead], 500)
    
    print("Test completed!")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
