# ECG System Documentation

## Hardware Data Reading Specifications

### Timer Intervals and Reading Rates
- **Primary Timer**: 50ms interval (20 FPS)
- **Secondary Timer**: 100ms interval (10 FPS) 
- **Overlay Timer**: 100ms interval (10 FPS)
- **Recording Timer**: 33ms interval (~30 FPS)

### Data Reading Per Update Cycle
- **Target**: Up to 20 readings per 50ms GUI update
- **Maximum**: 400 readings per second (20 updates/sec × 20 readings/update)
- **Hardware Dependent**: Actual rate varies based on device capability

### ECG Display Buffers
- **Buffer Size**: 1000 samples per ECG box
- **Time Window**: 4 seconds at 250 Hz sampling rate
- **Peaks Per Box**: 4-5 complete heartbeats at 72 BPM

### Serial Communication
- **Port**: Configurable (default from settings)
- **Baud Rate**: Configurable (default from settings)
- **Data Format**: 8-channel input converted to 12-lead display
- **Real-time Processing**: Medical-grade filtering applied

### Performance Metrics
- **Update Frequency**: 20 Hz (50ms intervals)
- **Data Processing**: Up to 20 readings per cycle
- **Display Refresh**: Real-time with 4-second rolling window
- **Memory Usage**: 1000 samples × 12 leads = 12,000 data points

### Technical Notes
- Hardware reading rate is independent of display buffer size
- Display shows last 1000 samples regardless of input rate
- Real-time conversion from 8-channel to 12-lead ECG
- Medical-grade smoothing algorithms applied to all data

## File Structure
```
src/ecg/twelve_lead_test.py - Main ECG processing
src/dashboard/dashboard.py - Real-time metrics display  
src/ecg/expanded_lead_view.py - Detailed lead analysis
src/utils/settings_manager.py - Hardware configuration
```

## Dependencies
- PyQt5 for GUI components
- NumPy for data processing
- SciPy for signal filtering
- Serial communication for hardware interface
- Matplotlib for plotting

## Configuration
- Sampling rates: 250Hz, 500Hz (configurable)
- Buffer sizes: 1000 samples per lead
- Timer intervals: 50ms, 100ms, 33ms
- Display refresh: Real-time updates

## Performance Characteristics
- **Input**: Up to 400 readings/second
- **Processing**: Real-time medical filtering
- **Output**: 12-lead ECG display with 4-second rolling window
- **Memory**: 12,000 data points (1000 × 12 leads)

## Hardware Compatibility
- Serial ports: Any available COM port
- Baud rates: Configurable (typically 9600-115200)
- Data format: 8-channel ECG input
- Output: 12-lead standard ECG display

## Real-time Processing Pipeline
1. **Hardware Input**: Serial data at configurable rate
2. **Buffer Management**: 1000 samples per lead
3. **Signal Processing**: Medical-grade filtering
4. **Lead Conversion**: 8-channel to 12-lead
5. **Display Update**: Real-time refresh at 20 FPS
6. **Memory Management**: Rolling 4-second window

## Technical Specifications
- **ECG Leads**: 12 standard leads (I, II, III, aVR, aVL, aVF, V1-V6)
- **Sampling Rate**: 250Hz or 500Hz (configurable)
- **Buffer Size**: 1000 samples per lead
- **Update Rate**: 20 Hz (50ms intervals)
- **Data Points**: Up to 400 readings/second from hardware
- **Display Window**: 4 seconds rolling window
- **Memory Usage**: 12,000 data points total (1000 × 12 leads)

## Performance Optimization
- **Real-time Processing**: Medical-grade algorithms
- **Memory Efficient**: Rolling buffer system
- **Hardware Adaptive**: Adjusts to device capabilities
- **Display Optimized**: 20 FPS refresh rate
- **Signal Quality**: Medical-grade filtering applied

## Troubleshooting
- **Serial Connection**: Check port and baud rate
- **Data Rate**: Verify hardware capability
- **Buffer Overflow**: Monitor 1000-sample limits
- **Timer Issues**: Check 50ms interval configuration
- **Display Problems**: Verify 12-lead conversion

## Version History
- v1.0: Initial ECG processing system
- v1.1: Added real-time filtering
- v1.2: Enhanced 8-to-12 lead conversion
- v1.3: Optimized memory usage with rolling buffers

## Future Enhancements
- **Higher Sampling Rates**: Support for 1000Hz+
- **Advanced Filtering**: AI-based signal processing
- **Cloud Integration**: Real-time data streaming
- **Mobile Support**: Cross-platform compatibility

## Support and Maintenance
- **Documentation**: This file
- **Code Comments**: Inline technical details
- **Version Control**: Git repository
- **Issue Tracking**: GitHub issues for bug reports

## License and Usage
- **Open Source**: MIT License
- **Medical Use**: For educational/research purposes only
- **Hardware**: Compatible with standard ECG devices
- **Software**: Cross-platform PyQt5 application

---
*Last Updated: $(date)*
*ECG System Version: 1.3*
*Hardware Compatibility: Standard ECG devices*
*Sampling Rate: 250Hz/500Hz (configurable)*

