# ECG Monitor - Mac Executable

## 📱 Ready-to-Use Application

The ECG Monitor application has been packaged as a standalone Mac application that can run on any Mac without requiring Python or dependencies to be installed.

## 🚀 How to Run

### Option 1: Double-Click (Recommended)
1. Navigate to the `dist/` folder
2. Double-click `ECG_Monitor.app`
3. The application will launch automatically

### Option 2: Using Terminal
```bash
# From the project root directory
./launch_ecg_monitor.sh
```

### Option 3: Using Finder
1. Open Finder
2. Navigate to `dist/ECG_Monitor.app`
3. Right-click → "Open" (first time only - macOS security)
4. Click "Open" in the security dialog

## 📦 What's Included

The `ECG_Monitor.app` bundle contains:
- **Complete ECG Monitor Application** (271 MB)
- **All Dependencies**: PyQt5, NumPy, SciPy, Matplotlib, PyQtGraph, etc.
- **All Assets**: Images, sounds, configuration files
- **Email Configuration Template**: For crash reporting setup
- **Demo Data**: CSV files for testing

## 🔧 Features Available

✅ **12-Lead ECG Analysis** - Real-time ECG signal processing  
✅ **Dashboard Interface** - Live metrics and visualization  
✅ **PDF Report Generation** - Comprehensive ECG reports  
✅ **Recent Reports Panel** - In-app report management  
✅ **Crash Logger** - Hidden diagnostic system (triple-click heart rate)  
✅ **Demo Mode** - Test without hardware  
✅ **Email Reporting** - Configure via `.env` file  

## 📧 Email Setup (Optional)

To enable email crash reporting:

1. **Copy the template**:
   ```bash
   cp email_config_template.txt .env
   ```

2. **Edit `.env`** with your Gmail credentials:
   ```
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   EMAIL_RECIPIENT=your_email@gmail.com
   ```

3. **Generate Gmail App Password**:
   - Enable 2-Factor Authentication
   - Go to Google Account → Security → App passwords
   - Generate password for "Mail"
   - Use this password (not your regular password)

## 🖥️ System Requirements

- **macOS**: 10.13 (High Sierra) or later
- **Architecture**: Apple Silicon (M1/M2) or Intel x64
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space

## 🚨 First Launch Notes

- **Security Warning**: macOS may show a security warning on first launch
- **Solution**: Right-click the app → "Open" → Click "Open" in the dialog
- **Alternative**: Go to System Preferences → Security & Privacy → Allow the app

## 📁 File Structure

```
dist/
├── ECG_Monitor.app/          # Main application bundle
│   ├── Contents/
│   │   ├── MacOS/           # Executable files
│   │   ├── Resources/       # Assets and data files
│   │   ├── Frameworks/      # Python and library frameworks
│   │   └── Info.plist       # App metadata
│   └── _CodeSignature/      # Code signing (if applicable)
└── ECG_Monitor/             # Alternative executable format
```

## 🔍 Troubleshooting

### App Won't Launch
1. **Check macOS version**: Requires 10.13+
2. **Security settings**: Allow the app in System Preferences
3. **Permissions**: Ensure you have read/execute permissions

### Missing Features
1. **Demo Mode**: Should work out of the box
2. **Email Reporting**: Requires `.env` configuration
3. **Hardware Connection**: Requires compatible ECG device

### Performance Issues
1. **Close other applications** to free up RAM
2. **Restart the application** if it becomes slow
3. **Check Activity Monitor** for resource usage

## 📞 Support

For issues or questions:
- **Crash Reports**: Triple-click heart rate metric → Send via email
- **Logs**: Check `logs/` directory for detailed logs
- **Configuration**: Edit `ecg_settings.json` for advanced settings

## 🎯 Distribution

To share the application:
1. **Zip the entire `dist/` folder**
2. **Include this README** for setup instructions
3. **Include `email_config_template.txt`** for email setup
4. **Test on target Mac** before distribution

---

**Built with PyInstaller** | **ECG Monitor v1.0.0** | **Deckmount Technologies**
