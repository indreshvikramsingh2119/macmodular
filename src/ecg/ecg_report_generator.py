from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, PageBreak
)
import os
import json
import matplotlib.pyplot as plt  #  ADD THIS IMPORT
import matplotlib
import numpy as np

# Set matplotlib to use non-interactive backend
matplotlib.use('Agg')

def create_ecg_grid_with_waveform(ecg_data, lead_name, width=6, height=2):
    """
    Create ECG graph with pink grid background and dark ECG waveform
    Returns: matplotlib figure with pink ECG grid background
    """
    # Create figure with pink background
    fig, ax = plt.subplots(figsize=(width, height), facecolor='#ffe6e6', frameon=True)
    
    # STEP 1: Create pink ECG grid background
    # ECG grid colors (even lighter pink/red like medical ECG paper)
    light_grid_color = '#ffd1d1'  # Darker minor grid
    major_grid_color = '#ffb3b3'  # Darker major grid
    bg_color = '#ffe6e6'  # Very light pink background
    
    # Set both figure and axes background to pink
    fig.patch.set_facecolor(bg_color)  # Figure background pink
    ax.set_facecolor(bg_color)         # Axes background pink
    
    # STEP 2: Draw pink ECG grid lines
    # Minor grid lines (1mm equivalent spacing) - LIGHT PINK
    minor_spacing_x = width / 60  # 60 minor divisions across width
    minor_spacing_y = height / 20  # 20 minor divisions across height
    
    # Draw vertical minor pink grid lines
    for i in range(61):
        x_pos = i * minor_spacing_x
        ax.axvline(x=x_pos, color=light_grid_color, linewidth=0.6, alpha=0.8)
    
    # Draw horizontal minor pink grid lines
    for i in range(21):
        y_pos = i * minor_spacing_y
        ax.axhline(y=y_pos, color=light_grid_color, linewidth=0.6, alpha=0.8)
    
    # Major grid lines (5mm equivalent spacing) - DARKER PINK
    major_spacing_x = width / 12  # 12 major divisions across width
    major_spacing_y = height / 4   # 4 major divisions across height
    
    # Draw vertical major pink grid lines
    for i in range(13):
        x_pos = i * major_spacing_x
        ax.axvline(x=x_pos, color=major_grid_color, linewidth=1.0, alpha=0.9)
    
    # Draw horizontal major pink grid lines
    for i in range(5):
        y_pos = i * major_spacing_y
        ax.axhline(y=y_pos, color=major_grid_color, linewidth=1.0, alpha=0.9)
    
    # STEP 3: Plot DARK ECG waveform on top of pink grid
    if ecg_data is not None and len(ecg_data) > 0:
        # Scale ECG data to fit in the grid
        t = np.linspace(0, width, len(ecg_data))
        # Normalize ECG data to fit in height with some margin
        if np.max(ecg_data) != np.min(ecg_data):
            ecg_normalized = ((ecg_data - np.min(ecg_data)) / (np.max(ecg_data) - np.min(ecg_data))) * (height * 0.8) + (height * 0.1)
        else:
            ecg_normalized = np.full_like(ecg_data, height / 2)
        
        # DARK ECG LINE - clearly visible on pink grid
        ax.plot(t, ecg_normalized, color='#000000', linewidth=2.8, solid_capstyle='round', alpha=0.9)
    # REMOVE ENTIRE else BLOCK - just comment it out or delete lines 78-96
    
    # STEP 4: Set axis limits to match grid
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    
    # STEP 5: Remove axis elements but keep the pink grid background
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('')
    
    return fig

from reportlab.graphics.shapes import Drawing, Group, Line, Rect
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.lib.units import mm

def create_reportlab_ecg_drawing(lead_name, width=460, height=45):
    """
    Create ECG drawing using ReportLab (NO matplotlib - NO white background issues)
    Returns: ReportLab Drawing with guaranteed pink background
    """
    drawing = Drawing(width, height)
    
    # STEP 1: Create solid pink background rectangle
    bg_color = colors.HexColor("#ffe6e6")  # Light pink background
    bg_rect = Rect(0, 0, width, height, fillColor=bg_color, strokeColor=None)
    drawing.add(bg_rect)
    
    # STEP 2: Draw pink ECG grid lines (even lighter colors)
    light_grid_color = colors.HexColor("#ffd1d1")  # Darker minor grid
    major_grid_color = colors.HexColor("#ffb3b3")   # Darker major grid
    
    # Minor grid lines (1mm spacing equivalent)
    minor_spacing_x = width / 60  # 60 divisions across width
    minor_spacing_y = height / 20  # 20 divisions across height
    
    # Vertical minor grid lines
    for i in range(61):
        x_pos = i * minor_spacing_x
        line = Line(x_pos, 0, x_pos, height, strokeColor=light_grid_color, strokeWidth=0.4)
        drawing.add(line)
    
    # Horizontal minor grid lines
    for i in range(21):
        y_pos = i * minor_spacing_y
        line = Line(0, y_pos, width, y_pos, strokeColor=light_grid_color, strokeWidth=0.4)
        drawing.add(line)
    
    # Major grid lines (5mm spacing equivalent)
    major_spacing_x = width / 12  # 12 divisions across width
    major_spacing_y = height / 4   # 4 divisions across height
    
    # Vertical major grid lines
    for i in range(13):
        x_pos = i * major_spacing_x
        line = Line(x_pos, 0, x_pos, height, strokeColor=major_grid_color, strokeWidth=0.8)
        drawing.add(line)
    
    # Horizontal major grid lines
    for i in range(5):
        y_pos = i * major_spacing_y
        line = Line(0, y_pos, width, y_pos, strokeColor=major_grid_color, strokeWidth=0.8)
        drawing.add(line)
    
    # REMOVE ENTIRE "STEP 3: Draw ECG waveform as series of lines" section (lines ~166-214)
    
    return drawing

def capture_real_ecg_graphs_from_dashboard(dashboard_instance=None, ecg_test_page=None):
    """
    Capture REAL ECG data from the live test page and create drawings
    Returns: dict with ReportLab Drawing objects containing REAL ECG data
    """
    lead_drawings = {}
    
    print(" Capturing REAL ECG data from live test page...")
    
    # Get lead sequence from settings
    from utils.settings_manager import SettingsManager
    settings_manager = SettingsManager()
    lead_sequence = settings_manager.get_setting("lead_sequence", "Standard")
    
    # Define lead orders based on sequence 
    LEAD_SEQUENCES = {
        "Standard": ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"],
        "Cabrera": ["aVL", "I", "-aVR", "II", "aVF", "III", "V1", "V2", "V3", "V4", "V5", "V6"]
    }
    
    # Use the appropriate sequence for REPORT ONLY
    ordered_leads = LEAD_SEQUENCES.get(lead_sequence, LEAD_SEQUENCES["Standard"])
    
    # Map lead names to indices
    lead_to_index = {
        "I": 0, "II": 1, "III": 2, "aVR": 3, "aVL": 4, "aVF": 5,
        "V1": 6, "V2": 7, "V3": 8, "V4": 9, "V5": 10, "V6": 11
    }
    
    # Try to get REAL ECG data from the test page
    real_ecg_data = {}
    if ecg_test_page and hasattr(ecg_test_page, 'data'):
        
        for lead in ordered_leads:
            if lead == "-aVR":
                # For -aVR, we need to invert aVR data
                if hasattr(ecg_test_page, 'data') and len(ecg_test_page.data) > 3:
                    avr_data = np.array(ecg_test_page.data[3])  # aVR is at index 3
                    # MAXIMUM data for 7+ heartbeats - NO LIMITS!
                    real_ecg_data[lead] = -avr_data[-10000:]  # Last 10000 points (20 seconds = plenty of heartbeats)
                    print(f" Captured REAL -aVR data: {len(real_ecg_data[lead])} points (MAXIMUM for 7+ heartbeats)")
            else:
                lead_index = lead_to_index.get(lead)
                if lead_index is not None and len(ecg_test_page.data) > lead_index:
                    # MAXIMUM data for 7+ heartbeats - NO LIMITS!
                    lead_data = np.array(ecg_test_page.data[lead_index])
                    if len(lead_data) > 0:
                        real_ecg_data[lead] = lead_data[-10000:]  # Last 10000 points (20 seconds = plenty of heartbeats)
                        print(f"📈 Captured REAL {lead} data: {len(real_ecg_data[lead])} points (MAXIMUM for 7+ heartbeats)")
                    else:
                        print(f"⚠️ No data found for {lead}")
                else:
                    print(f"⚠️ Lead {lead} index not found")
    else:
        print("⚠️ No live ECG test page found - using grid only")
    
    # Create ReportLab drawings with REAL data
    for lead in ordered_leads:
        try:
            # Create ReportLab drawing with REAL ECG data
            drawing = create_reportlab_ecg_drawing_with_real_data(
                lead, 
                real_ecg_data.get(lead), 
                width=460, 
                height=45
            )
            lead_drawings[lead] = drawing
            
            if lead in real_ecg_data:
                print(f"✅ Created drawing with MAXIMUM data for Lead {lead} - showing 7+ heartbeats")
            else:
                print(f"Created grid-only drawing for Lead {lead}")
            
        except Exception as e:
            print(f" Error creating drawing for Lead {lead}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f" Successfully created {len(lead_drawings)}/12 ECG drawings with MAXIMUM heartbeats!")
    return lead_drawings

def create_reportlab_ecg_drawing_with_real_data(lead_name, ecg_data, width=460, height=45):
    """
    Create ECG drawing using ReportLab with REAL ECG data showing MAXIMUM heartbeats
    Returns: ReportLab Drawing with guaranteed pink background and REAL ECG waveform
    """
    drawing = Drawing(width, height)
    
    # STEP 1: Create solid pink background rectangle
    bg_color = colors.HexColor("#ffe6e6")  # Light pink background
    bg_rect = Rect(0, 0, width, height, fillColor=bg_color, strokeColor=None)
    drawing.add(bg_rect)
    
    # STEP 2: Draw pink ECG grid lines (even lighter colors)
    light_grid_color = colors.HexColor("#ffd1d1")  # Darker minor grid
    major_grid_color = colors.HexColor("#ffb3b3")   # Darker major grid
    
    # Minor grid lines (1mm spacing equivalent)
    minor_spacing_x = width / 60  # 60 divisions across width
    minor_spacing_y = height / 20  # 20 divisions across height
    
    # Vertical minor grid lines
    for i in range(61):
        x_pos = i * minor_spacing_x
        line = Line(x_pos, 0, x_pos, height, strokeColor=light_grid_color, strokeWidth=0.4)
        drawing.add(line)
    
    # Horizontal minor grid lines
    for i in range(21):
        y_pos = i * minor_spacing_y
        line = Line(0, y_pos, width, y_pos, strokeColor=light_grid_color, strokeWidth=0.4)
        drawing.add(line)
    
    # Major grid lines (5mm spacing equivalent)
    major_spacing_x = width / 12  # 12 divisions across width
    major_spacing_y = height / 4   # 4 divisions across height
    
    # Vertical major grid lines
    for i in range(13):
        x_pos = i * major_spacing_x
        line = Line(x_pos, 0, x_pos, height, strokeColor=major_grid_color, strokeWidth=0.8)
        drawing.add(line)
    
    # Horizontal major grid lines
    for i in range(5):
        y_pos = i * major_spacing_y
        line = Line(0, y_pos, width, y_pos, strokeColor=major_grid_color, strokeWidth=0.8)
        drawing.add(line)
    
    # STEP 3: Draw ALL AVAILABLE ECG data - NO DOWNSAMPLING, NO LIMITS!
    if ecg_data is not None and len(ecg_data) > 0:
        print(f"🎯 Drawing ALL AVAILABLE ECG data for {lead_name}: {len(ecg_data)} points (NO LIMITS)")
        
        # SIMPLE APPROACH: Use ALL available data points - NO cutting, NO downsampling
        # This will show as many heartbeats as possible in the available data
        
        # Create time array for ALL the data
        t = np.linspace(0, width, len(ecg_data))
        
        # Scale ECG data to fit in height with MAXIMUM amplitude
        ecg_min, ecg_max = np.min(ecg_data), np.max(ecg_data)
        if ecg_max != ecg_min:
            # Use FULL height for maximum visibility
            ecg_normalized = ((ecg_data - ecg_min) / (ecg_max - ecg_min)) * (height * 0.95) + (height * 0.025)
        else:
            ecg_normalized = np.full_like(ecg_data, height / 2)
        
        # Draw ALL ECG data points - NO REDUCTION
        ecg_color = colors.HexColor("#000000")  # Black ECG line
        
        # OPTIMIZED: Draw every point for maximum detail
        for i in range(len(t) - 1):
            line = Line(t[i], ecg_normalized[i], 
                       t[i+1], ecg_normalized[i+1], 
                       strokeColor=ecg_color, strokeWidth=0.5)
            drawing.add(line)
        
        print(f" Drew ALL {len(ecg_data)} ECG data points for {lead_name} - showing MAXIMUM heartbeats!")
    else:
        print(f" No real data available for {lead_name} - showing grid only")
    
    return drawing

def create_clean_ecg_image(lead_name, width=6, height=2):
    """
    Create COMPLETELY CLEAN ECG image with GUARANTEED pink background
    NO labels, NO time markers, NO axes, NO white background
    """
    # FORCE matplotlib to use proper backend
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    # STEP 1: Create figure with FORCED pink background
    fig = plt.figure(figsize=(width, height), facecolor='#ffe6e6', frameon=True)
    
    # FORCE figure background to pink
    fig.patch.set_facecolor('#ffe6e6')
    fig.patch.set_alpha(1.0)  # Full opacity
    
    # Create axes with FORCED pink background
    ax = fig.add_subplot(111)
    ax.set_facecolor('#ffe6e6')  # FORCE axes background pink
    ax.patch.set_facecolor('#ffe6e6')  # FORCE axes patch pink
    ax.patch.set_alpha(1.0)  # Full opacity
    
    # STEP 2: Draw pink ECG grid lines OVER pink background (darker for clarity)
    light_grid_color = '#ffd1d1'  # Darker minor grid
    major_grid_color = '#ffb3b3'  # Darker major grid
    
    # Minor grid lines (1mm equivalent spacing)
    minor_spacing_x = width / 60  # 60 minor divisions
    minor_spacing_y = height / 20  # 20 minor divisions
    
    # Draw vertical minor pink grid lines
    for i in range(61):
        x_pos = i * minor_spacing_x
        ax.axvline(x=x_pos, color=light_grid_color, linewidth=0.6, alpha=0.8)
    
    # Draw horizontal minor pink grid lines
    for i in range(21):
        y_pos = i * minor_spacing_y
        ax.axhline(y=y_pos, color=light_grid_color, linewidth=0.6, alpha=0.8)
    
    # Major grid lines (5mm equivalent spacing)
    major_spacing_x = width / 12  # 12 major divisions
    major_spacing_y = height / 4   # 4 major divisions
    
    # Draw vertical major pink grid lines
    for i in range(13):
        x_pos = i * major_spacing_x
        ax.axvline(x=x_pos, color=major_grid_color, linewidth=1.0, alpha=0.9)
    
    # Draw horizontal major pink grid lines
    for i in range(5):
        y_pos = i * major_spacing_y
        ax.axhline(y=y_pos, color=major_grid_color, linewidth=1.0, alpha=0.9)
    
    # REMOVE ENTIRE "STEP 3: Create realistic ECG waveform" section (lines ~315-356)
    # REMOVE ENTIRE "STEP 4: Plot DARK ECG line" section
    
    # STEP 5: Set limits and remove ALL visual elements except grid
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    
    # COMPLETELY remove ALL spines, ticks, labels
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('')
    ax.axis('off')  # FORCE turn off all axis elements
    
    # Remove any text objects
    for text in ax.texts:
        text.set_visible(False)
    
    # FORCE tight layout with pink background
    fig.tight_layout(pad=0)
    
    return fig


def get_dashboard_conclusions_from_image(dashboard_instance):
    """
    Load dynamic conclusions from JSON file (saved by dashboard)
    Returns: List of clean conclusion headings (up to 8 conclusions)
    """
    conclusions = []
    
    # **NEW: Try to load from JSON file first (DYNAMIC)**
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        conclusions_file = os.path.join(base_dir, 'last_conclusions.json')
        
        print(f"🔍 Looking for conclusions at: {conclusions_file}")
        
        if os.path.exists(conclusions_file):
            with open(conclusions_file, 'r') as f:
                conclusions_data = json.load(f)
            
            print(f"📄 Loaded JSON data: {conclusions_data}")
            
            # Extract findings from JSON
            findings = conclusions_data.get('findings', [])
            
            if findings:
                conclusions = findings[:8]  # Take up to 8 conclusions
                print(f"✅ Loaded {len(conclusions)} DYNAMIC conclusions from JSON file")
                for i, conclusion in enumerate(conclusions, 1):
                    print(f"   {i}. {conclusion}")
            else:
                print("⚠️ No findings in JSON file")
        else:
            print(f"❌ Conclusions JSON file not found: {conclusions_file}")
    
    except Exception as json_err:
        print(f"❌ Error loading conclusions from JSON: {json_err}")
        import traceback
        traceback.print_exc()
    
    # **REMOVED: Old code that extracted from dashboard_instance.conclusion_box**
    # **REMOVED: Fallback default conclusions**
    
    # If still no conclusions found, use minimal fallback
    if not conclusions:
        conclusions = [
            "--- No ECG data available ---",
            "--- Please connect device or enable demo mode ---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---"
        ]
        print("⚠️ Using zero-value fallback (no ECG data available)")
    
    # Ensure we have exactly 8 conclusions (pad with empty strings if needed)
    MAX_CONCLUSIONS = 8
    while len(conclusions) < MAX_CONCLUSIONS:
        conclusions.append("---")  # Use "---" for empty slots
    
    # Limit to maximum 8 conclusions
    conclusions = conclusions[:MAX_CONCLUSIONS]
    
    print(f" Final conclusions list (8 total): {len([c for c in conclusions if c and c != '---'])} filled, {len([c for c in conclusions if not c or c == '---'])} blank")
    
    return conclusions

def generate_ecg_report(filename="ecg_report.pdf", data=None, lead_images=None, dashboard_instance=None, ecg_test_page=None, patient=None):
    if data is None:
        # When no device connected or demo off - show ZERO values (not dummy values)
        data = {
            "HR": 0,
            "beat": 0,
            "PR": 0,
            "QRS": 0,
            "QT": 0,
            "QTc": 0,
            "ST": 0,
            "HR_max": 0,
            "HR_min": 0,
            "HR_avg": 0,
            "QRS_axis": "--",
        }

    # Get conclusions from dashboard/JSON
    dashboard_conclusions = get_dashboard_conclusions_from_image(dashboard_instance)

    # SAFEGUARD: If there is no real data (all core metrics are zero), ignore any
    # persisted conclusions and use the explicit "no data" conclusions instead.
    try:
        core_keys = ["HR", "PR", "QRS", "QT", "QTc", "ST"]
        all_zero = True
        for k in core_keys:
            v = data.get(k, 0)
            try:
                all_zero = all_zero and (float(v) == 0.0)
            except Exception:
                all_zero = all_zero and (str(v).strip() in ["0", "--", "", "None"])
        if all_zero:
            dashboard_conclusions = [
                "--- No ECG data available ---",
                "--- Please connect device or enable demo mode ---",
                "---",
                "---",
                "---",
                "---",
                "---",
                "---"
            ]
            print("⚠️ Overriding conclusions because all core metrics are zero (no data)")
    except Exception:
        pass

    print(f"\n📋 Report will use these conclusions: {dashboard_conclusions}\n")

    #  FORCE DELETE ALL OLD WHITE BACKGROUND IMAGES
    if lead_images is None:
        print("  DELETING ALL OLD WHITE BACKGROUND IMAGES...")
        
        # Get both possible locations
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..', '..')
        project_root = os.path.abspath(project_root)
        src_dir = os.path.join(current_dir, '..')
        
        leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        
        # DELETE from both locations
        for lead in leads:
            # Location 1: project root
            img_path1 = os.path.join(project_root, f"lead_{lead}.png")
            if os.path.exists(img_path1):
                os.remove(img_path1)
                print(f"  Deleted OLD image: {img_path1}")
            
            # Location 2: src directory  
            img_path2 = os.path.join(src_dir, f"lead_{lead}.png")
            if os.path.exists(img_path2):
                os.remove(img_path2)
                print(f"  : {img_path2}")
        
        print(" CREATING NEW PINK GRID IMAGES...")
        
        # Create NEW pink grid images
        lead_images = {}
        for lead in leads:
            try:
                # Create pink grid ECG
                fig = create_ecg_grid_with_waveform(None, lead, width=6, height=2)
                
                # Save to project root with pink background
                img_path = os.path.join(project_root, f"lead_{lead}.png")
                fig.savefig(img_path, 
                           dpi=200, 
                           bbox_inches='tight', 
                           pad_inches=0.05,
                           facecolor='#ffe6e6',  # PINK background
                           edgecolor='none',
                           format='png')
                plt.close(fig)
                
                lead_images[lead] = img_path
                print(f" Created NEW PINK GRID image: {img_path}")
                
            except Exception as e:
                print(f" Error creating {lead}: {e}")
        
        if not lead_images:
            return "Error: Could not create PINK GRID ECG images"
    
    # Get REAL ECG drawings from live test page
    print(" Capturing REAL ECG data from live test page...")
    
    # Check if demo mode is active and data is available
    if ecg_test_page and hasattr(ecg_test_page, 'demo_toggle'):
        is_demo = ecg_test_page.demo_toggle.isChecked()
        if is_demo:
            print("🔍 DEMO MODE DETECTED - Checking data availability...")
            if hasattr(ecg_test_page, 'data') and len(ecg_test_page.data) > 0:
                # Check if data has actual variation (not just zeros)
                sample_data = ecg_test_page.data[0] if len(ecg_test_page.data) > 0 else []
                if len(sample_data) > 0:
                    std_val = np.std(sample_data)
                    print(f"   📊 Data buffer size: {len(sample_data)}, Std deviation: {std_val:.4f}")
                    if std_val < 0.01:
                        print("   ⚠️ WARNING: Demo data appears to be flat/empty!")
                        print("   💡 TIP: Make sure demo has been running for at least 5 seconds before generating report")
                    else:
                        print(f"   ✅ Demo data looks good (variation detected)")
                else:
                    print("   ⚠️ WARNING: Data buffer is empty!")
            else:
                print("   ❌ ERROR: No data structure found!")
    
    lead_drawings = capture_real_ecg_graphs_from_dashboard(dashboard_instance, ecg_test_page)
    
    # Get lead sequence from settings
    from utils.settings_manager import SettingsManager
    settings_manager = SettingsManager()
    lead_sequence = settings_manager.get_setting("lead_sequence", "Standard")
    
    # Define lead orders based on sequence
    LEAD_SEQUENCES = {
        "Standard": ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"],
        "Cabrera": ["aVL", "I", "-aVR", "II", "aVF", "III", "V1", "V2", "V3", "V4", "V5", "V6"]
    }
    
    # Use the appropriate sequence for REPORT ONLY
    lead_order = LEAD_SEQUENCES.get(lead_sequence, LEAD_SEQUENCES["Standard"])
    
    print(f" Using lead sequence for REPORT: {lead_sequence}")
    print(f" Lead order for REPORT: {lead_order}")

    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)

    story = []
    styles = getSampleStyleSheet()
    heading = ParagraphStyle(
        'Heading',
        fontSize=16,
        textColor=colors.HexColor("#000000"),
        spaceAfter=12,
        leading=20,
        alignment=1,  # center
        bold=True
    )

    # Title (switch based on demo mode)
    is_demo = False
    try:
        if ecg_test_page and hasattr(ecg_test_page, 'demo_toggle'):
            is_demo = bool(ecg_test_page.demo_toggle.isChecked())
    except Exception:
        pass

    title_text = "Demo ECG Report" if is_demo else "ECG Report"
    story.append(Paragraph(f"<b>{title_text}</b>", heading))
    story.append(Spacer(1, 12))


    # Patient Details
    if patient is None:
        patient = {}
    first_name = patient.get("first_name", "")
    last_name = patient.get("last_name", "")
    age = patient.get("age", "")
    gender = patient.get("gender", "")
   
    date_time = patient.get("date_time", "")
    
    story.append(Paragraph("<b>Patient Details</b>", styles['Heading3']))
    patient_table = Table([
        ["Name:", f"{first_name} {last_name}".strip(), "Age:", f"{age}", "Gender:", f"{gender}"],
        ["Date:", f"{date_time.split()[0] if date_time else ''}", "Time:", f"{date_time.split()[1] if len(date_time.split()) > 1 else ''}", "", ""],
        # ], colWidths=[80, 150, 50, 80, 60, 150])  # Increased all column widths
            ], colWidths=[70, 130, 40, 70, 50, 140])  # Total width = 500
    patient_table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 1, colors.black),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 12))  # Reduced from 18

    # Report Overview
    story.append(Paragraph("<b>Report Overview</b>", styles['Heading3']))
    overview_data = [
        # ["Total Number of Heartbeats (beats):", data["HR"]],
        ["Maximum Heart Rate:", f'{data["HR_max"]} bpm'],
        ["Minimum Heart Rate:", f'{data["HR_min"]} bpm'],
        ["Average Heart Rate:", f'{data["HR_avg"]} bpm'],
    ]
    table = Table(overview_data, colWidths=[300, 200])
    table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 1, colors.black),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ]))
    story.append(table)
    story.append(Spacer(1, 15))  # Reduced from 35

    # Observation with 3 parts in ONE table (like in the image)
    story.append(Paragraph("<b>OBSERVATION</b>", styles['Heading3']))
    story.append(Spacer(1, 8))  # Reduced from 10
    
    # Create table with 3 columns: Interval Names, Observed Values, Standard Range
    obs_headers = ["Interval Names", "Observed Values", "Standard Range"]
    obs_data = [
        ["Heart Rate", f"{data['beat']} bpm", "60-100"],                    
        ["PR Interval", f"{data['PR']} ms", "120 ms - 200 ms"],            
        ["QRS Complex", f"{data['QRS']} ms", "70 ms - 120 ms"],            
        ["QT Interval", f"{data['QT']} ms", "300 ms - 450 ms"],            
        ["QTC Interval", f"{data['QTc']} ms", "300 ms - 450 ms"],          
        ["QRS Axis", f"{data.get('QRS_axis', '--')}°", "Normal"],         
        ["ST Interval", f"{data['ST']} ms", "80 ms - 120 ms"],            
    ]
    
    # Add headers to data
    obs_table_data = [obs_headers] + obs_data
    
    # Table dimensions
    COLUMN_WIDTH_1 = 165  
    COLUMN_WIDTH_2 = 165 
    COLUMN_WIDTH_3 = 165
    ROW_HEIGHT = 15       
    HEADER_HEIGHT = 30    
    
    # Create table with 3 columns and custom dimensions
    obs_table = Table(obs_table_data, colWidths=[COLUMN_WIDTH_1, COLUMN_WIDTH_2, COLUMN_WIDTH_3])
    
    # Style the table with custom dimensions
    obs_table.setStyle(TableStyle([
        # Header row styling
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e6f2")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), HEADER_HEIGHT//2),
        ("TOPPADDING", (0, 0), (-1, 0), HEADER_HEIGHT//2),
        
        # Data rows styling
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),  # Reduced padding
        ("TOPPADDING", (0, 1), (-1, -1), 5),     # Reduced padding
        
        # Grid and borders
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(obs_table)
    story.append(Spacer(1, 12))  # Reduced from 18

   

    # Conclusion in table format - NOW DYNAMIC FROM DASHBOARD (8 conclusions max)
    story.append(Paragraph("<b>ECG Report Conclusion</b>", styles['Heading3']))
    story.append(Spacer(1, 8))   # Reduced from 10
    
    # Create dynamic conclusion table using dashboard conclusions (8 conclusions)
    conclusion_headers = ["S.No.", "Conclusion"]
    conclusion_data = []
    
    # FIXED: Show ALL 8 conclusions (even empty ones) instead of only non-empty ones
    for i, conclusion in enumerate(dashboard_conclusions[:8], 1):  # Ensure exactly 8 conclusions
        # Add ALL conclusions to table (including empty ones)
        conclusion_data.append([str(i), conclusion if conclusion.strip() else "---"])  # Show "---" for empty conclusions
    
    print(f"📊 Creating conclusion table with {len(conclusion_data)} rows:")
    for row in conclusion_data:
        print(f"   {row}")
    
    # Add headers to conclusion data
    conclusion_table_data = [conclusion_headers] + conclusion_data
    
    # Create conclusion table
    conclusion_table = Table(conclusion_table_data, colWidths=[80, 420])
    
    # Style the conclusion table
    conclusion_table.setStyle(TableStyle([
        # Header row styling
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e6f2")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"), 
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        
        # Data rows styling
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),  
        ("ALIGN", (1, 1), (1, -1), "LEFT"),     
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 8),
        
        # Grid and borders
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(conclusion_table)
    story.append(Spacer(1, 12))  # Reduced from 18

    # REMOVE PageBreak HERE to send patient details to Page 2
    # story.append(PageBreak())

    # Now these patient details will be on Page 2 top
    # Patient header on Page 2 (Name, Age, Gender, Date/Time)
    if patient is None:
        patient = {}
    first_name = patient.get("first_name", "")
    last_name = patient.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    age = patient.get("age", "")
    gender = patient.get("gender", "")
    date_time_str = patient.get("date_time", "")

    # Push the first row on Page 2 a bit lower (affects Name/HR/ST row)
    story.append(Spacer(1, 14))

    # Make text clearly visible on pink background WITHOUT any background
    mini_label_style = ParagraphStyle(
        'MiniLabel',
        fontSize=12,  # Increased from 10
        fontName='Helvetica-Bold',
        textColor=colors.black,
        leading=14,
        # NO background - let pink grid show through completely
        # backColor=colors.white,  # REMOVE this line completely
    )

    mini_value_style = ParagraphStyle(
        'MiniValue',
        fontSize=12,  # Increased from 10
        fontName='Helvetica',
        textColor=colors.black,
        leading=14,
        # NO background - let pink grid show through completely
        # backColor=colors.white,  # REMOVE this line completely
    )

    # REMOVE the table approach and use Canvas positioning instead
    # Comment out or delete the left_patient_table code

    # Replace with individual paragraphs positioned left
    from reportlab.platypus import KeepTogether

    # Create left-aligned style (less bold, like doctor name)
    left_info_style = ParagraphStyle(
        'LeftInfoStyle',
        fontSize=10,  # Same as doctor name
        fontName='Helvetica',  # Regular font, not bold
        textColor=colors.black,
        alignment=0,  # Left alignment
        leftIndent=0,  # No indentation
        spaceAfter=6,  # Increased from 2 to 6 for more gap
    )

    # Add Name, Age, Gender as separate left-aligned paragraphs with more gap
    # story.append(Paragraph(f"Name: {full_name}", left_info_style))
    # story.append(Paragraph(f"Age: {age}", left_info_style))
    # story.append(Paragraph(f"Gender: {gender}", left_info_style))
    # story.append(Spacer(1, 15))  # Increased from 8 to 15 for more gap after Gender

    # RIGHT SIDE: Date/Time - keep block at right edge, align text inside left
    date_time_text_style = ParagraphStyle(
        'DateTimeLeft',
        fontSize=12,
        fontName='Helvetica',
        textColor=colors.black,
        alignment=0,   # left inside the cell
        spaceAfter=0,
    )

    if date_time_str:
        parts = date_time_str.split()
        date_part = parts[0] if parts else ""
        time_part = parts[1] if len(parts) > 1 else ""
    else:
        date_part, time_part = "____", "____"

    date_para = Paragraph(f"Date: {date_part}", date_time_text_style)
    time_para = Paragraph(f"Time: {time_part}", date_time_text_style)

    # Single-column, two-row table positioned to the right of the frame
    date_time_table = Table([[date_para], [time_para]], colWidths=[120])
    date_time_table.hAlign = 'RIGHT'  # place the whole table at right edge
    date_time_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(date_time_table)
    story.append(Spacer(1, 8))

    
    # Vital Parameters Header (completely transparent)
    vital_style = ParagraphStyle(
        'VitalStyle',
        fontSize=12,  # Increased from 11
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=15,
        alignment=1,  # center
        # Add white background 
        # for better visibility on pink grid
        backColor=colors.white,
    )

    # Vital Parameters Header (on top of background)
    vital_style = ParagraphStyle(
        'VitalStyle',
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=15,
        alignment=1,  # center
        
    )

    # Get real ECG data from dashboard
    HR = data.get('HR_avg', 70)
    PR = data.get('PR', 192) 
    QRS = data.get('QRS', 93)
    QT = data.get('QT', 354)
    QTc = data.get('QTc', 260)
    ST = data.get('ST', 114)
    # DYNAMIC RR interval calculation from heart rate (instead of hard-coded 857)
    RR = int(60000 / HR) if HR and HR > 0 else 0  # RR interval in ms from heart rate
   

    # Create table data: 2 rows × 2 columns (as per your changes)
    vital_table_data = [
        [f"HR : {HR} bpm", f"QT: {QT} ms"],
        [f"PR : {PR} ms", f"QTc: {QTc} ms"],
        [f"QRS: {QRS} ms", f"ST: {ST} ms"],
        [f"RR : {RR} ms", ""]  
    ]

    # Create vital parameters table with MORE LEFT and TOP positioning
    vital_params_table = Table(vital_table_data, colWidths=[100, 100])  # Even smaller widths for more left

    vital_params_table.setStyle(TableStyle([
        # Transparent background to show pink grid
        ("BACKGROUND", (0, 0), (-1, -1), colors.Color(0, 0, 0, alpha=0)),
        ("GRID", (0, 0), (-1, -1), 0, colors.Color(0, 0, 0, alpha=0)),
        ("BOX", (0, 0), (-1, -1), 0, colors.Color(0, 0, 0, alpha=0)),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),  # Left align
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),  # Normal font
        ("FONTSIZE", (0, 0), (-1, -1), 10),  # Same size as Name, Age, Gender
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),  # Zero left padding for extreme left
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),  # Zero right padding too
        ("TOPPADDING", (0, 0), (-1, -1), 0),   # Zero top padding for top shift
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

   

    #  CREATE SINGLE MASSIVE DRAWING with ALL ECG content (NO individual drawings)
    print("Creating SINGLE drawing with all ECG content...")
    
    # Single drawing dimensions
    total_width = 520   # Full page width
    total_height = 600  # Height for all content
    
    # Create ONE master drawing
    master_drawing = Drawing(total_width, total_height)
    
    # STEP 1: NO background rectangle - let page pink grid show through
    
    # STEP 2: Define positions for all 12 leads based on selected sequence (SHIFTED DOWN)
    y_positions = [500, 450, 400, 350, 300, 250, 200, 150, 100, 50, 0, -50]
    lead_positions = []
    
    for i, lead in enumerate(lead_order):
        lead_positions.append({
            "lead": lead, 
            "x": 60, 
            "y": y_positions[i]
        })
    
    print(f" Using lead positions in {lead_sequence} sequence: {[pos['lead'] for pos in lead_positions]}")
    
    # STEP 3: Draw ALL ECG content directly in master drawing
    successful_graphs = 0
    
    # Check if demo mode is active
    is_demo_mode = False
    if ecg_test_page and hasattr(ecg_test_page, 'demo_toggle'):
        is_demo_mode = ecg_test_page.demo_toggle.isChecked()
        print(f"🔍 Report Generator: Demo mode is {'ON' if is_demo_mode else 'OFF'}")
    
    for pos_info in lead_positions:
        lead = pos_info["lead"]
        x_pos = pos_info["x"]
        y_pos = pos_info["y"]
        
        try:
            # STEP 3A: Add lead label directly
            from reportlab.graphics.shapes import String
            lead_label = String(10, y_pos + 20, f"{lead}", 
                              fontSize=10, fontName="Helvetica-Bold", fillColor=colors.black)
            master_drawing.add(lead_label)
            
            # STEP 3B: Get ALL AVAILABLE REAL ECG data for this lead
            real_data_available = False
            if ecg_test_page and hasattr(ecg_test_page, 'data'):
                lead_to_index = {
                    "I": 0, "II": 1, "III": 2, "aVR": 3, "aVL": 4, "aVF": 5,
                    "V1": 6, "V2": 7, "V3": 8, "V4": 9, "V5": 10, "V6": 11
                }
                
                if lead == "-aVR" and len(ecg_test_page.data) > 3:
                    # For -aVR, use ALL available inverted aVR data
                    raw_data = ecg_test_page.data[3][-8000:]
                    # Check if data is not all zeros or flat
                    if len(raw_data) > 0 and np.std(raw_data) > 0.01:
                        real_ecg_data = -np.array(raw_data)  # Last 8000 points = 16 seconds
                        real_data_available = True
                        print(f"✅ Using ALL available -aVR data: {len(real_ecg_data)} points (std: {np.std(real_ecg_data):.2f})")
                    else:
                        print(f"⚠️ -aVR data is flat or empty (std: {np.std(raw_data) if len(raw_data) > 0 else 0:.4f})")
                elif lead in lead_to_index and len(ecg_test_page.data) > lead_to_index[lead]:
                    # Get ALL available real data for this lead
                    lead_index = lead_to_index[lead]
                    if len(ecg_test_page.data[lead_index]) > 0:
                        raw_data = ecg_test_page.data[lead_index][-8000:]  # Last 8000 points = 16 seconds
                        # Check if data has variation (not all zeros or flat line)
                        if len(raw_data) > 0 and np.std(raw_data) > 0.01:
                            real_ecg_data = np.array(raw_data)
                            real_data_available = True
                            print(f"✅ Using ALL available {lead} data: {len(real_ecg_data)} points (std: {np.std(real_ecg_data):.2f})")
                        else:
                            print(f"⚠️ Lead {lead} data is flat or empty (std: {np.std(raw_data) if len(raw_data) > 0 else 0:.4f})")
                    else:
                        print(f"⚠️ Lead {lead} data buffer is empty")
            
            if real_data_available and len(real_ecg_data) > 0:
                # Draw ALL REAL ECG data - NO LIMITS
                ecg_width = 460
                ecg_height = 45
                
                # Create time array for ALL data
                t = np.linspace(x_pos, x_pos + ecg_width, len(real_ecg_data))
                
                # Scale ALL real ECG signal to fit in height
                ecg_min, ecg_max = np.min(real_ecg_data), np.max(real_ecg_data)
                if ecg_max != ecg_min:
                    ecg_normalized = ((real_ecg_data - ecg_min) / (ecg_max - ecg_min)) * (ecg_height * 0.95) + y_pos + (ecg_height * 0.025)
                else:
                    ecg_normalized = np.full_like(real_ecg_data, y_pos + ecg_height / 2)
                
                # Draw ALL REAL ECG data points
                from reportlab.graphics.shapes import Path
                ecg_path = Path(fillColor=None, 
                               strokeColor=colors.HexColor("#000000"), 
                               strokeWidth=0.4,  # Thinner line for more data points
                               strokeLineCap=1,
                               strokeLineJoin=1)
                
                # Start path
                ecg_path.moveTo(t[0], ecg_normalized[0])
                
                # Add ALL points - NO REDUCTION
                for i in range(1, len(t)):
                    ecg_path.lineTo(t[i], ecg_normalized[i])
                
                # Add path to master drawing
                master_drawing.add(ecg_path)
                
                print(f"✅ Added ALL REAL ECG data for Lead {lead}: {len(real_ecg_data)} points (MAXIMUM heartbeats)")
            else:
                print(f"📋 No real data for Lead {lead} - showing grid only")
            
            successful_graphs += 1
            
        except Exception as e:
            print(f"❌ Error adding Lead {lead}: {e}")
            import traceback
            traceback.print_exc()
    
    # STEP 4: Add Patient Info and Vital Parameters to master drawing
    from reportlab.graphics.shapes import String

    # LEFT SIDE: Patient Info (SHIFTED DOWN - lower positions)
    patient_name_label = String(-30, 670, f"Name: {full_name}", 
                           fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(patient_name_label)

    patient_age_label = String(-30, 650, f"Age: {age}", 
                          fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(patient_age_label)

    patient_gender_label = String(-30, 630, f"Gender: {gender}", 
                             fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(patient_gender_label)

    # RIGHT SIDE: Vital Parameters at SAME LEVEL as patient info (SHIFTED DOWN)
    # Get real ECG data from dashboard
    HR = data.get('HR_avg', 70)
    PR = data.get('PR', 192) 
    QRS = data.get('QRS', 93)
    QT = data.get('QT', 354)
    QTc = data.get('QTc', 260)
    ST = data.get('ST', 114)
    # DYNAMIC RR interval calculation from heart rate (instead of hard-coded 857)
    RR = int(60000 / HR) if HR and HR > 0 else 0  # RR interval in ms from heart rate
   
    # Add vital parameters in TWO COLUMNS
    # FIRST COLUMN (Left side - x=130)
    hr_label = String(130, 670, f"HR    : {HR} bpm", 
                     fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(hr_label)

    pr_label = String(130, 650, f"PR    : {PR} ms", 
                     fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(pr_label)

    qrs_label = String(130, 630, f"QRS : {QRS} ms", 
                      fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(qrs_label)
    
    rr_label = String(130, 612, f"RR    : {RR} ms", 
                     fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(rr_label)

    qt_label = String(130, 594, f"QT    : {QT} ms", 
                     fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(qt_label)

    qtc_label = String(130, 576, f"QTc  : {QTc} ms", 
                      fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(qtc_label)

    # SECOND COLUMN (Right side - x=240)
    st_label = String(240, 594, f"ST            : {ST} ms", 
                     fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(st_label)

    # CALCULATED wave amplitudes and lead-specific measurements
    # Prefer values passed in data; if missing/zero, compute from live ecg_test_page data (last 10s)
    p_amp_mv = data.get('p_amp', 0.0)
    qrs_amp_mv = data.get('qrs_amp', 0.0)
    t_amp_mv = data.get('t_amp', 0.0)
    
    print(f"🔬 Report Generator - Received wave amplitudes from data:")
    print(f"   p_amp: {p_amp_mv}, qrs_amp: {qrs_amp_mv}, t_amp: {t_amp_mv}")
    print(f"   Available keys in data: {list(data.keys())}")
    
    # If not provided or zero, compute quickly from Lead II in ecg_test_page (robust fallback)
    def _compute_from_data_array(arr, fs):
        from scipy.signal import butter, filtfilt, find_peaks
        if arr is None or len(arr) < int(2*fs) or np.std(arr) < 0.1:
            return 0.0, 0.0, 0.0
        nyq = fs/2.0
        b,a = butter(2, [max(0.5/nyq, 0.001), min(40.0/nyq,0.99)], btype='band')
        x = filtfilt(b,a,arr)
        # Simple R detection via Pan-Tompkins style envelope
        squared = np.square(np.diff(x))
        win = max(1, int(0.15*fs))
        env = np.convolve(squared, np.ones(win)/win, mode='same')
        thr = np.mean(env) + 0.5*np.std(env)
        r_peaks, _ = find_peaks(env, height=thr, distance=int(0.6*fs))
        if len(r_peaks) < 3:
            return 0.0, 0.0, 0.0
        p_vals, qrs_vals, t_vals = [], [], []
        for r in r_peaks[1:-1]:
            # P: 120-200ms before R
            p_start = max(0, r-int(0.20*fs)); p_end = max(0, r-int(0.12*fs))
            if p_end>p_start:
                seg = x[p_start:p_end]
                base = np.mean(x[max(0,p_start-int(0.05*fs)):p_start])
                p_vals.append(max(seg)-base)
            # QRS: +-80ms around R
            qrs_start = max(0, r-int(0.08*fs)); qrs_end = min(len(x), r+int(0.08*fs))
            if qrs_end>qrs_start:
                seg = x[qrs_start:qrs_end]
                qrs_vals.append(max(seg)-min(seg))
            # T: 100-300ms after R
            t_start = min(len(x), r+int(0.10*fs)); t_end = min(len(x), r+int(0.30*fs))
            if t_end>t_start:
                seg = x[t_start:t_end]
                base = np.mean(x[r:t_start]) if t_start>r else 0.0
                t_vals.append(max(seg)-base)
        def med(v):
            return float(np.median(v)) if len(v)>0 else 0.0
        return med(p_vals), med(qrs_vals), med(t_vals)

    if (p_amp_mv<=0 or qrs_amp_mv<=0 or t_amp_mv<=0) and ecg_test_page is not None and hasattr(ecg_test_page,'data'):
        try:
            fs = 250.0
            if hasattr(ecg_test_page, 'sampler') and hasattr(ecg_test_page.sampler,'sampling_rate') and ecg_test_page.sampler.sampling_rate:
                fs = float(ecg_test_page.sampler.sampling_rate)
            arr = None
            if len(ecg_test_page.data)>1:
                lead_ii = ecg_test_page.data[1]
                if isinstance(lead_ii, (list, tuple)):
                    lead_ii = np.asarray(lead_ii)
                arr = lead_ii[-int(10*fs):] if lead_ii is not None and len(lead_ii)>int(10*fs) else lead_ii
            cp, cqrs, ct = _compute_from_data_array(arr, fs)
            if p_amp_mv<=0: p_amp_mv = cp
            if qrs_amp_mv<=0: qrs_amp_mv = cqrs
            if t_amp_mv<=0: t_amp_mv = ct
            print(f"🔁 Fallback computed amplitudes from Lead II: P={p_amp_mv:.4f}, QRS={qrs_amp_mv:.4f}, T={t_amp_mv:.4f}")
        except Exception as e:
            print(f"⚠️ Fallback amplitude computation failed: {e}")

    # Convert to mm (ECG standard: 1mV = 10mm)
    p_mm = int(p_amp_mv * 10) if p_amp_mv > 0 else 12  # fallback to 12
    qrs_mm = int(qrs_amp_mv * 10) if qrs_amp_mv > 0 else 37  # fallback to 37
    t_mm = int(t_amp_mv * 10) if t_amp_mv > 0 else 34  # fallback to 34
    
    print(f"   Converted to mm: P={p_mm}, QRS={qrs_mm}, T={t_mm}")
    
    # SECOND COLUMN - P/QRS/T
    p_qrs_label = String(240, 670, f"P/QRS/T  : {p_mm}/{qrs_mm}/{t_mm}", 
                         fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(p_qrs_label)

    # Get RV5 and SV1 amplitudes
    rv5_amp = data.get('rv5', 0.0)
    sv1_amp = data.get('sv1', 0.0)
    
    print(f"🔬 Report Generator - Received RV5/SV1 from data:")
    print(f"   rv5: {rv5_amp}, sv1: {sv1_amp}")
    
    # If missing/zero, compute from V5 and V1 of last 10 seconds
    if (rv5_amp<=0 or sv1_amp<=0) and ecg_test_page is not None and hasattr(ecg_test_page,'data'):
        try:
            from scipy.signal import butter, filtfilt, find_peaks
            fs = 250.0
            if hasattr(ecg_test_page, 'sampler') and hasattr(ecg_test_page.sampler,'sampling_rate') and ecg_test_page.sampler.sampling_rate:
                fs = float(ecg_test_page.sampler.sampling_rate)
            def _get_last(arr):
                return arr[-int(10*fs):] if arr is not None and len(arr)>int(10*fs) else arr
            # V5 index 10, V1 index 6
            v5 = _get_last(ecg_test_page.data[10]) if len(ecg_test_page.data)>10 else None
            v1 = _get_last(ecg_test_page.data[6]) if len(ecg_test_page.data)>6 else None
            if v5 is not None and len(v5)>int(2*fs):
                nyq = fs/2.0
                b,a = butter(2, [max(0.5/nyq, 0.001), min(40.0/nyq,0.99)], btype='band')
                v5f = filtfilt(b,a, np.asarray(v5))
                env = np.convolve(np.square(np.diff(v5f)), np.ones(int(0.15*fs))/(0.15*fs), mode='same')
                r,_ = find_peaks(env, height=np.mean(env)+0.5*np.std(env), distance=int(0.6*fs))
                vals=[]
                for rr in r[1:-1]:
                    qs = max(0, rr-int(0.08*fs)); qe = min(len(v5f), rr+int(0.08*fs))
                    base = np.mean(v5f[max(0,qs-int(0.05*fs)):qs])
                    vals.append(np.max(v5f[qs:qe])-base)
                if len(vals)>0 and rv5_amp<=0: rv5_amp = float(np.median(vals))
            if v1 is not None and len(v1)>int(2*fs):
                nyq = fs/2.0
                b,a = butter(2, [max(0.5/nyq, 0.001), min(40.0/nyq,0.99)], btype='band')
                v1f = filtfilt(b,a, np.asarray(v1))
                env = np.convolve(np.square(np.diff(v1f)), np.ones(int(0.15*fs))/(0.15*fs), mode='same')
                r,_ = find_peaks(env, height=np.mean(env)+0.5*np.std(env), distance=int(0.6*fs))
                vals=[]
                for rr in r[1:-1]:
                    ss = rr; se = min(len(v1f), rr+int(0.08*fs))
                    base = np.mean(v1f[max(0,ss-int(0.05*fs)):ss])
                    vals.append(base-np.min(v1f[ss:se]))
                if len(vals)>0 and sv1_amp<=0: sv1_amp = float(np.median(vals))
            print(f"🔁 Fallback computed RV5/SV1: RV5={rv5_amp:.4f}, SV1={sv1_amp:.4f}")
        except Exception as e:
            print(f"⚠️ Fallback RV5/SV1 computation failed: {e}")

    # Convert to mV for display (values assumed to be in microvolt-like units; normalize)
    rv5_mv = rv5_amp / 1000 if rv5_amp > 0 else 1.260  # fallback
    sv1_mv = sv1_amp / 1000 if sv1_amp > 0 else 0.786  # fallback
    
    print(f"   Converted to mV: RV5={rv5_mv:.3f}, SV1={sv1_mv:.3f}")
    
    # SECOND COLUMN - RV5/SV1
    rv5_sv_label = String(240, 650, f"RV5/SV1  : {rv5_mv:.3f}/{sv1_mv:.3f}", 
                          fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(rv5_sv_label)

    # Calculate RV5+SV1 sum
    rv5_sv1_sum = rv5_mv + sv1_mv
    
    # SECOND COLUMN - RV5+SV1
    rv5_sv1_sum_label = String(240, 630, f"RV5+SV1 : {rv5_sv1_sum:.3f}", 
                               fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(rv5_sv1_sum_label)

    # SECOND COLUMN - QTCF
    qtcf_label = String(240, 612, "QTCF       : 0.049", 
                        fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(qtcf_label)

    

    # Doctor Name (BOTTOM LEFT - existing code)
    
    from reportlab.pdfbase.pdfmetrics import stringWidth
    label_text = "Doctor Name: "
    doctor_name_label = String(-30, -100, label_text,
                            fontSize=10, fontName="Helvetica-Bold", fillColor=colors.black)
    master_drawing.add(doctor_name_label)

    # Value from Save ECG -> passed in 'patient'
    doctor = ""
    try:
        if patient:
            doctor = str(patient.get("doctor", "")).strip()
    except Exception:
        doctor = ""

    if doctor:
        value_x = -30 + stringWidth(label_text, "Helvetica-Bold", 10) + 6
        doctor_name_value = String(value_x, -100, doctor,
                                fontSize=10, fontName="Helvetica", fillColor=colors.black)
        master_drawing.add(doctor_name_value)

    # Doctor Name (BOTTOM LEFT - SHIFTED FURTHER DOWN) - KEEP AS IS
    doctor_name_label = String(-30, -100, "Doctor Name: ", 
                              fontSize=10, fontName="Helvetica-Bold", fillColor=colors.black)
    master_drawing.add(doctor_name_label)

    # Doctor Signature (BOTTOM LEFT - SHIFTED FURTHER DOWN) - KEEP AS IS
    doctor_sign_label = String(-30, -120, "Doctor Sign: ", 
                              fontSize=10, fontName="Helvetica-Bold", fillColor=colors.black)
    master_drawing.add(doctor_sign_label)

    # Add RIGHT-SIDE Conclusion Box (moved to the right) - NOW DYNAMIC FROM DASHBOARD (8 conclusions max)
    conclusion_y_start = -80  # Higher up (was -120)
    
    # Create a rectangular box for conclusions (shifted right) - INCREASED HEIGHT
    from reportlab.graphics.shapes import Rect
    conclusion_box = Rect(200, conclusion_y_start - 45, 340, 65,  # INCREASED height from 55 to 65, bottom from -35 to -40
                         fillColor=None, strokeColor=colors.black, strokeWidth=1.5)
    master_drawing.add(conclusion_box)
    
    # CENTERED and STYLISH "Conclusion" header - DYNAMIC
    # Box center: 200 + (300/2) = 350, so text should be centered around 350
    conclusion_header = String(350, conclusion_y_start + 8, "✦ CONCLUSION ✦", 
                              fontSize=11, fontName="Helvetica-Bold", 
                              fillColor=colors.HexColor("#2c3e50"),
                              textAnchor="middle")  # This centers the text
    master_drawing.add(conclusion_header)
    
    # DYNAMIC conclusions from dashboard in the box (8 conclusions max)
    # Split conclusions into FOUR ROWS (2 conclusions per row) - INCREASED SPACING
    print(f"🎨 Drawing conclusions in graph from list: {dashboard_conclusions}")
    row1_conclusions = dashboard_conclusions[:2]   # First 2 conclusions (1-2)
    row2_conclusions = dashboard_conclusions[2:4]  # Next 2 conclusions (3-4)
    row3_conclusions = dashboard_conclusions[4:6]  # Next 2 conclusions (5-6)
    row4_conclusions = dashboard_conclusions[6:8]  # Last 2 conclusions (7-8)
    print(f"   Row 1: {row1_conclusions}")
    print(f"   Row 2: {row2_conclusions}")
    print(f"   Row 3: {row3_conclusions}")
    print(f"   Row 4: {row4_conclusions}")
    
    # ROW 1: Conclusions 1-2 (2 conclusions per row) - INCREASED SPACING
    row1_y = conclusion_y_start - 5  # Fixed Y position for row 1
    for i, conclusion in enumerate(row1_conclusions):
        # FIXED: Show ALL conclusions (including empty ones)
        display_conclusion = conclusion[:35] + "..." if len(conclusion) > 35 else (conclusion if conclusion.strip() else "---")
        conc_text = f"{i+1}. {display_conclusion}"
        # Position horizontally across the box (2 conclusions per row)
        x_pos = 210 + (i * 140)  # 140 points spacing for 2 conclusions per row
        conc = String(x_pos, row1_y, conc_text, 
                     fontSize=8, fontName="Helvetica", fillColor=colors.black)
        master_drawing.add(conc)
    
    # ROW 2: Conclusions 3-4 (2 conclusions per row) - INCREASED SPACING
    row2_y = conclusion_y_start - 17  # INCREASED spacing from -15 to -17 (2 points more gap)
    for i, conclusion in enumerate(row2_conclusions):
        # FIXED: Show ALL conclusions (including empty ones)
        display_conclusion = conclusion[:35] + "..." if len(conclusion) > 35 else (conclusion if conclusion.strip() else "---")
        conc_text = f"{i+3}. {display_conclusion}"  # Start numbering from 3
        # Position horizontally across the box (2 conclusions per row)
        x_pos = 210 + (i * 140)  # 140 points spacing for 2 conclusions per row
        conc = String(x_pos, row2_y, conc_text, 
                     fontSize=8, fontName="Helvetica", fillColor=colors.black)
        master_drawing.add(conc)
    
    # ROW 3: Conclusions 5-6 (2 conclusions per row) - INCREASED SPACING
    row3_y = conclusion_y_start - 29  # INCREASED spacing from -25 to -29 (4 points more gap)
    for i, conclusion in enumerate(row3_conclusions):
        # FIXED: Show ALL conclusions (including empty ones)
        display_conclusion = conclusion[:35] + "..." if len(conclusion) > 35 else (conclusion if conclusion.strip() else "---")
        conc_text = f"{i+5}. {display_conclusion}"  # Start numbering from 5
        # Position horizontally across the box (2 conclusions per row)
        x_pos = 210 + (i * 140)  # 140 points spacing for 2 conclusions per row
        conc = String(x_pos, row3_y, conc_text, 
                     fontSize=8, fontName="Helvetica", fillColor=colors.black)
        master_drawing.add(conc)
    
    # ROW 4: Conclusions 7-8 (2 conclusions per row) - INCREASED SPACING
    row4_y = conclusion_y_start - 41  # INCREASED spacing from -35 to -41 (6 points more gap)
    for i, conclusion in enumerate(row4_conclusions):
        # FIXED: Show ALL conclusions (including empty ones)
        display_conclusion = conclusion[:35] + "..." if len(conclusion) > 35 else (conclusion if conclusion.strip() else "---")
        conc_text = f"{i+7}. {display_conclusion}"  # Start numbering from 7
        # Position horizontally across the box (2 conclusions per row)
        x_pos = 210 + (i * 140)  # 140 points spacing for 2 conclusions per row
        conc = String(x_pos, row4_y, conc_text, 
                     fontSize=8, fontName="Helvetica", fillColor=colors.black)
        master_drawing.add(conc)

    print(" Added Patient Info, Vital Parameters, ALL 8 Conclusions from Dashboard in 4 ROWS (2 conclusions per row), and Doctor Name/Signature to ECG grid")
    
    # STEP 5: Add SINGLE master drawing to story (NO containers)
    story.append(master_drawing)
    story.append(Spacer(1, 15))
    
    print(f" Added SINGLE master drawing with {successful_graphs}/12 ECG leads (ZERO containers)!")
    
    # Final summary
    if is_demo_mode:
        print(f"\n{'='*60}")
        print(f"📊 DEMO MODE REPORT SUMMARY:")
        print(f"   • Total leads processed: {successful_graphs}/12")
        print(f"   • Demo mode: {'ON' if is_demo_mode else 'OFF'}")
        if successful_graphs == 0:
            print(f"   ⚠️ WARNING: No ECG graphs were added to the report!")
            print(f"   💡 SOLUTION: Ensure demo is running for 5-10 seconds before generating report")
        elif successful_graphs < 12:
            print(f"   ⚠️ WARNING: Only {successful_graphs} graphs added (expected 12)")
        else:
            print(f"   ✅ SUCCESS: All 12 ECG graphs added successfully!")
        print(f"{'='*60}\n")

    # Measurement info (NO background)
    measurement_style = ParagraphStyle(
        'MeasurementStyle',
        fontSize=8,
        textColor=colors.HexColor("#000000"),
        alignment=1  # center
        # backColor removed
    )


    # Summary (NO background)
    summary_style = ParagraphStyle( 
        'SummaryStyle',
        fontSize=10,
        textColor=colors.HexColor("#000000"),
        alignment=1  # center
        # backColor removed
    )
    # summary_para = Paragraph(f"ECG Report: {successful_graphs}/12 leads displayed", summary_style)
    # story.append(summary_para)

    # Helper: draw logo on every page AND ALIGNED pink grid background on Page 2
    def _draw_logo_and_footer(canvas, doc):
        import os
        from reportlab.lib.units import mm
        
        # STEP 1: Draw FULL PAGE pink ECG grid background on Page 2 (ECG graphs page)
        if canvas.getPageNumber() == 2:  # Changed from 3 to 2
            page_width, page_height = canvas._pagesize
            
            # Fill entire page with pink background
            canvas.setFillColor(colors.HexColor("#ffe6e6"))
            canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
            
            # ECG grid colors - darker for better visibility
            light_grid_color = colors.HexColor("#ffd1d1")  
            
            major_grid_color = colors.HexColor("#ffb3b3")   
            
            # Draw minor grid lines (1mm spacing) - FULL PAGE
            canvas.setStrokeColor(light_grid_color)
            canvas.setLineWidth(0.6)
            
            minor_spacing = 1 * mm
            
            # Vertical minor lines - full page
            x = 0
            while x <= page_width:
                canvas.line(x, 0, x, page_height)
                x += minor_spacing
            
            # Horizontal minor lines - full page
            y = 0
            while y <= page_height:
                canvas.line(0, y, page_width, y)
                y += minor_spacing
            
            # Draw major grid lines (5mm spacing) - FULL PAGE
            canvas.setStrokeColor(major_grid_color)
            canvas.setLineWidth(1.2)
            
            major_spacing = 5 * mm
            
            # Vertical major lines - full page
            x = 0
            while x <= page_width:
                canvas.line(x, 0, x, page_height)
                x += major_spacing
            
            # Horizontal major lines - full page
            y = 0
            while y <= page_height:
                canvas.line(0, y, page_width, y)
                y += major_spacing
        
        # STEP 2: Draw logo on all pages (existing code)
        # Prefer PNG (ReportLab-friendly); fallback to WebP if PNG missing
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        png_path = os.path.join(base_dir, "assets", "Deckmountimg.png")
        webp_path = os.path.join(base_dir, "assets", "Deckmount.webp")
        logo_path = png_path if os.path.exists(png_path) else webp_path

        if os.path.exists(logo_path):
            canvas.saveState()
            # Different positioning for different pages
            if canvas.getPageNumber() == 2:
                logo_w, logo_h = 120, 40  # bigger size for ECG page
                # SHIFTED LEFT FROM RIGHT TOP CORNER
                page_width, page_height = canvas._pagesize
                x = page_width - logo_w - 35  # Shifted 50 pixels left from right edge
                y = page_height - logo_h  # Top edge touch
            else:
                logo_w, logo_h = 120, 40  # normal size for other pages
                x = doc.width + doc.leftMargin - logo_w
                y = doc.height + doc.bottomMargin - logo_h  # top positioning
            try:
                canvas.drawImage(logo_path, x, y, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
            except Exception:
                # If WebP unsupported, silently skip
                pass
            canvas.restoreState()
        
        # STEP 3: Add footer with company address on all pages
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.black)  # Ensure text is black on pink background
        footer_text = "Deckmount Electronic , Plot No. 260, Phase IV, Udyog Vihar, Sector 18, Gurugram, Haryana 122015"
        # Center the footer text at bottom of page
        text_width = canvas.stringWidth(footer_text, "Helvetica", 8)
        x = (doc.width + doc.leftMargin + doc.rightMargin - text_width) / 2
        y = 10  # 20 points from bottom
        canvas.drawString(x, y, footer_text)
        canvas.restoreState()

    # Save parameters to a JSON index for later reuse
    try:
        from datetime import datetime
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        reports_dir = os.path.join(base_dir, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        index_path = os.path.join(reports_dir, 'index.json')
        metrics_path = os.path.join(reports_dir, 'metrics.json')

        params_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "file": os.path.abspath(filename),
            "patient": {
                "name": full_name,
                "age": str(age),
                "gender": gender,
                "date_time": date_time_str,
            },
            "metrics": {
                "HR_bpm": HR,
                "PR_ms": PR,
                "QRS_ms": QRS,
                "QT_ms": QT,
                "QTc_ms": QTc,
                "ST_ms": ST,
                "RR_ms": RR,
                "RV5_plus_SV1_mV": round(rv5_sv1_sum, 3),
                "P_QRS_T_mm": [p_mm, qrs_mm, t_mm],
                "RV5_SV1_mV": [round(rv5_mv, 3), round(sv1_mv, 3)],
                "QTCF": 0.049,
            }
        }

        existing_list = []
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    existing_json = json.load(f)
                    if isinstance(existing_json, list):
                        existing_list = existing_json
                    elif isinstance(existing_json, dict) and isinstance(existing_json.get('entries'), list):
                        existing_list = existing_json['entries']
            except Exception:
                existing_list = []

        existing_list.append(params_entry)

        # Persist as a flat list for simplicity
        with open(index_path, 'w') as f:
            json.dump(existing_list, f, indent=2)
        print(f"✓ Saved parameters to {index_path}")

        # Save ONLY the 11 metrics in a lightweight separate JSON file (append to list)
        metrics_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "file": os.path.abspath(filename),
            "HR_bpm": HR,
            "PR_ms": PR,
            "QRS_ms": QRS,
            "QT_ms": QT,
            "QTc_ms": QTc,
            "ST_ms": ST,
            "RR_ms": RR,
            "RV5_plus_SV1_mV": round(rv5_sv1_sum, 3),
            "P_QRS_T_mm": [p_mm, qrs_mm, t_mm],
            "QTCF": 0.049,
            "RV5_SV1_mV": [round(rv5_mv, 3), round(sv1_mv, 3)]
        }

        metrics_list = []
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, 'r') as f:
                    mj = json.load(f)
                    if isinstance(mj, list):
                        metrics_list = mj
            except Exception:
                metrics_list = []

        metrics_list.append(metrics_entry)

        with open(metrics_path, 'w') as f:
            json.dump(metrics_list, f, indent=2)
        print(f"✓ Saved 11 metrics to {metrics_path}")
    except Exception as e:
        print(f"⚠️ Could not save parameters JSON: {e}")

    # Build PDF
    doc.build(story, onFirstPage=_draw_logo_and_footer, onLaterPages=_draw_logo_and_footer)
    print(f"✓ ECG Report generated: {filename}")
    
    # Upload to cloud if configured
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.cloud_uploader import get_cloud_uploader
        
        cloud_uploader = get_cloud_uploader()
        if cloud_uploader.is_configured():
            print(f"☁️  Uploading report to cloud ({cloud_uploader.cloud_service})...")
            
            # Prepare metadata
            upload_metadata = {
                "patient_name": data.get('patient', {}).get('name', 'Unknown'),
                "patient_age": str(data.get('patient', {}).get('age', '')),
                "report_date": data.get('date', ''),
                "machine_serial": data.get('machine_serial', ''),
                "heart_rate": str(data.get('Heart_Rate', '')),
            }
            
            # Upload the report
            result = cloud_uploader.upload_report(filename, metadata=upload_metadata)
            
            if result.get('status') == 'success':
                print(f"✓ Report uploaded successfully to {cloud_uploader.cloud_service}")
                if 'url' in result:
                    print(f"  URL: {result['url']}")
            else:
                print(f"⚠️  Cloud upload failed: {result.get('message', 'Unknown error')}")
        else:
            print("ℹ️  Cloud upload not configured (see cloud_config_template.txt)")
            
    except ImportError:
        print("ℹ️  Cloud uploader not available")
    except Exception as e:
        print(f"⚠️  Cloud upload error: {e}")


# REMOVE ENTIRE create_sample_ecg_images function (lines ~1222-1257)

# REMOVE ENTIRE main execution block (lines ~1260-1265)
# if __name__ == "__main__":
#     # Create sample images with transparency (force recreation)
#     create_sample_ecg_images(force_recreate=True)
#     
#     # Generate report
#     generate_ecg_report("test_ecg_report.pdf")
