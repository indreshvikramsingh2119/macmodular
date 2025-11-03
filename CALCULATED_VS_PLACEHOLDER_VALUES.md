# ECG Monitor - Calculated vs Placeholder Values

## Summary of What IS and IS NOT Calculated

---

## ✅ **CALCULATED VALUES** (Real-time from ECG signal)

### **Dashboard & 12-Lead Page:**
1. **Heart Rate (HR)** - ✅ Calculated from R-peak intervals (Pan-Tompkins algorithm)
2. **PR Interval** - ✅ Calculated using derivative-based P-wave detection
3. **QRS Duration** - ✅ Calculated from Q-onset to S-end
4. **QT Interval** - ✅ Calculated from Q-onset to T-wave end
5. **QTc Interval (Corrected)** - ✅ Calculated using Bazett's formula: QT / √RR
6. **ST Segment** - ✅ Calculated as elevation/depression from baseline
7. **QRS Axis** - ✅ Calculated from Lead I and aVF using vector analysis
8. **RR Interval** - ✅ Calculated as 60000/HR (ms between beats)
9. **Heart Rate Variability (HRV)** - ✅ Calculated as SDNN from RR intervals
10. **Stress Level** - ✅ Calculated from HRV thresholds (High/Moderate/Low)

### **Wave Amplitudes (for Report):**
11. **P Wave Amplitude** - ✅ Calculated from Lead II using peak detection
12. **QRS Amplitude** - ✅ Calculated from Lead II (R-peak minus baseline)
13. **T Wave Amplitude** - ✅ Calculated from Lead II T-wave detection
14. **RV5 Amplitude** - ✅ Calculated from Lead V5 R-peak
15. **SV1 Amplitude** - ✅ Calculated from Lead V1 S-wave
16. **RV5 + SV1** - ✅ Sum of above two values

### **Arrhythmia Detection:**
17. **Atrial Fibrillation** - ✅ Detected from irregular RR intervals
18. **Ventricular Tachycardia** - ✅ Detected from HR > 100 with wide QRS
19. **PVCs** - ✅ Detected from premature wide QRS complexes
20. **Bradycardia** - ✅ Detected from HR < 60
21. **Tachycardia** - ✅ Detected from HR > 100
22. **Normal Sinus Rhythm** - ✅ Default when no arrhythmias detected

### **Conclusions:**
23. **Live Conclusions** - ✅ Generated dynamically from current metrics
24. **PDF Report Conclusions** - ✅ Saved to last_conclusions.json and embedded in PDF

---

## ❌ **PLACEHOLDER/NOT FULLY CALCULATED** (Need Implementation)

### **In src/ecg/recording.py** (Lead12BlackPage - old/unused module):
- **All metrics** - Hardcoded placeholders (this module is not actively used)
- **PQRST peaks** - Placeholder arrays like `[100, 200, 300]`
- Note: This is dead code; the app uses `twelve_lead_test.py` instead

### **In Dashboard METRICS Panel (before our fix):**
- Previously showed "No metrics found" when no report was opened
- ✅ **FIXED**: Now shows live metrics by default

### **In Report PDF:**
- **P/QRS/T amplitudes (mm)** - ✅ Now calculated from wave_amplitudes
- **RV5/SV1 (mV)** - ✅ Now calculated from V5 and V1 leads
- **RV5+SV1 (mV)** - ✅ Now calculated as sum

### **Values That Could Be Enhanced:**
1. **QTCF (Fridericia formula)** - Currently returns `'--'`; could calculate as: QT / ∛RR
2. **Detailed P-wave analysis** - P-wave duration, PR segment
3. **Detailed T-wave analysis** - T-wave duration, morphology
4. **J-point analysis** - Precise J-point detection for ST calculation
5. **U-wave detection** - Not currently implemented

---

## 🎯 **Settings That WORK** (Fully Implemented)

### **Wave Speed (25mm/12.5mm/50mm):**
- ✅ Demo mode - WORKS
- ✅ Real hardware mode - WORKS (just fixed)
- Controls time window: 12.5mm = 20s, 25mm = 10s, 50mm = 5s

### **Wave Gain (5mm/10mm/20mm):**
- ✅ Demo mode - WORKS
- ✅ Real hardware mode - WORKS
- Controls amplitude scaling

---

## 📊 **Data Flow**

### **Dashboard → PDF Report:**
1. Metrics calculated in `twelve_lead_test.py`
2. Passed to Dashboard via `update_ecg_metrics()`
3. Dashboard stores in `metric_labels`
4. Report generation reads from Dashboard
5. Wave amplitudes calculated via `calculate_wave_amplitudes()`
6. All data embedded in PDF + saved to JSON twin

### **Dashboard → JSON Metrics:**
1. Report generation creates `ECG_Report_YYYYMMDD_HHMMSS.json`
2. Contains: patient, user (name/phone), machine_serial, metrics
3. Uploaded to AWS S3 alongside PDF
4. Admin panel can fetch and display

### **Report Selection → METRICS Box:**
1. User clicks report in Recent Reports
2. Calls `load_metrics_into_parameters(report_path)`
3. Reads JSON twin file
4. Displays in METRICS panel
5. Shows "LIVE" badge when viewing current session

---

## 🔧 **What Can Be Improved**

### **Immediate Needs:**
- None - all core metrics are calculated

### **Nice-to-Have Enhancements:**
1. **QTCF formula** - Add Fridericia correction as alternative to Bazett
2. **P-wave duration** - More detailed P-wave analysis
3. **T-wave morphology** - Detect inverted/biphasic T-waves
4. **QT dispersion** - Variation of QT across all 12 leads
5. **Sokolow-Lyon index** - LVH detection criteria
6. **Cornell voltage** - Alternative LVH criteria

---

## 🎨 **Current Status**

✅ **All critical ECG parameters are calculated in real-time**  
✅ **Wave speed and gain controls work in both demo and real mode**  
✅ **Reports contain actual calculated values (not hardcoded)**  
✅ **JSON twins save complete metrics for each report**  
✅ **Admin panel displays user/patient/machine/metrics from S3**  
✅ **METRICS panel shows live data by default**  

❌ **Only advanced/optional metrics (QTCF, detailed P/T analysis) are placeholders**

---

**Conclusion:** Your ECG monitor calculates all essential metrics in real-time. The only placeholders are advanced optional values that aren't critical for basic ECG analysis.

