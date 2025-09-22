# ECG Monitor Application

A comprehensive ECG monitoring application with 12-lead ECG analysis, real-time metrics calculation, and dashboard visualization.

## Features

- **12-Lead ECG Analysis**: Real-time ECG signal processing and visualization
- **Medical-Grade Signal Filtering**: Advanced filtering system for smooth, clean ECG waves like professional medical devices
- **Expanded Lead View**: Detailed analysis page for individual ECG leads with PQRST labeling
- **Live Metrics Calculation**: Heart Rate, PR Interval, QRS Duration, QTc Interval, QRS Axis, ST Segment
- **Arrhythmia Detection**: Automatic detection of various cardiac arrhythmias
- **Dashboard Interface**: Clean, modern dashboard with live metric updates
- **User Authentication**: Sign-in/sign-out functionality
- **PDF Report Generation**: Generate comprehensive ECG reports
- **Background GIF Support**: Animated background on sign-in screen
- **Real-time Data Processing**: Live ECG data acquisition and processing from hardware

## Project Structure

```
modularecg/
├── src/                    # Main application source code
│   ├── main.py            # Application entry point
│   ├── auth/              # Authentication modules
│   ├── dashboard/         # Dashboard and UI components
│   ├── ecg/               # ECG processing and analysis
│   ├── utils/             # Utility functions and helpers
│   └── nav_*.py           # Navigation components
├── assets/                # Images, GIFs, and other resources
├── requirements.txt       # Python dependencies
├── launch_app.bat        # Windows batch launcher
├── launch_app.ps1        # PowerShell launcher
├── users.json            # User data storage
└── clutter/              # Archived files and backups
```

## Installation

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Option 1: Using Batch File (Windows)
```bash
launch_app.bat
```

### Option 2: Using PowerShell Script
```bash
.\launch_app.ps1
```

### Option 3: Direct Python Execution
```bash
cd src
python main.py
```

## Usage

1. **Launch the application** using one of the methods above
2. **Sign in** with your credentials
3. **Navigate to the dashboard** to view live ECG metrics
4. **Click "ECG Lead Test 12"** to open the 12-lead ECG analysis page
5. **View live metrics** including Heart Rate, PR Interval, QRS Duration, QTc Interval, QRS Axis, and ST Segment
6. **Click on any ECG lead** to open the expanded lead view for detailed analysis
7. **View PQRST labeling** and detailed metrics for individual leads
8. **Monitor arrhythmia detection** in real-time

## ECG Metrics

The application calculates and displays the following metrics in real-time:

- **Heart Rate**: Beats per minute (BPM)
- **PR Interval**: Time from P-wave to QRS complex (ms)
- **QRS Duration**: Duration of QRS complex (ms)
- **QTc Interval**: Corrected QT interval using Bazett's formula (ms)
- **QRS Axis**: Electrical axis of the heart (degrees)
- **ST Segment**: ST elevation/depression (mV)

## Technical Details

- **Framework**: PyQt5 for GUI
- **Plotting**: PyQtGraph for real-time ECG visualization
- **Signal Processing**: NumPy and SciPy for ECG analysis
- **Medical-Grade Filtering**: Advanced filtering pipeline including Wiener filter, Gaussian smoothing, adaptive median filtering
- **Report Generation**: Matplotlib for static plots and PDF generation
- **Real-time Processing**: Live data acquisition and processing from ECG hardware
- **Arrhythmia Detection**: Pan-Tompkins algorithm for R-peak detection and cardiac rhythm analysis

## File Organization

- **Essential Files**: Only the necessary files for the application to run are kept in the root directory
- **Clutter Folder**: All test files, backups, and temporary files are moved to the `clutter/` folder for organization
- **Clean Structure**: The codebase is organized with clear separation of concerns

## Recent Updates

### Medical-Grade ECG Filtering System
- **Advanced Filtering Pipeline**: Implemented 8-stage filtering system for professional medical device-quality signals
- **Wiener Filter**: Statistical noise reduction optimized for ECG signals
- **Gaussian Smoothing**: Multi-stage smoothing for clean waveform appearance
- **Adaptive Median Filtering**: Dynamic noise removal based on signal characteristics
- **Real-time Smoothing**: Individual data point smoothing for live data processing

### Expanded Lead View
- **Detailed Analysis**: Click any ECG lead to open expanded analysis view
- **PQRST Labeling**: Automatic detection and labeling of cardiac waveform components
- **Enhanced Metrics**: Comprehensive metrics display with improved visibility
- **Arrhythmia Detection**: Real-time detection of various cardiac arrhythmias
- **Responsive UI**: Optimized layout and sizing for better user experience

### Signal Quality Improvements
- **Smooth Waveforms**: Medical-grade signal processing for clean, professional appearance
- **Stable Baseline**: Reduced drift and improved signal stability
- **Sharp R-peaks**: Enhanced peak detection for accurate heart rate calculation
- **Noise Reduction**: Comprehensive noise filtering for clear signal visualization

## Support

For issues or questions, please refer to the application documentation or contact the development team.