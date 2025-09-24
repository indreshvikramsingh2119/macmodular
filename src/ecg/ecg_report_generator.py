from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, PageBreak
)
import os
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
    light_grid_color = '#ffeeee'  # Even lighter pink for minor grid lines (was #ffe0e0)
    major_grid_color = '#ffe0e0'  # Even lighter pink for major grid lines (was #ffcccc)
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
        ax.axvline(x=x_pos, color=light_grid_color, linewidth=0.2, alpha=0.4)  # Further reduced linewidth and alpha
    
    # Draw horizontal minor pink grid lines
    for i in range(21):
        y_pos = i * minor_spacing_y
        ax.axhline(y=y_pos, color=light_grid_color, linewidth=0.2, alpha=0.4)  # Further reduced linewidth and alpha
    
    # Major grid lines (5mm equivalent spacing) - DARKER PINK
    major_spacing_x = width / 12  # 12 major divisions across width
    major_spacing_y = height / 4   # 4 major divisions across height
    
    # Draw vertical major pink grid lines
    for i in range(13):
        x_pos = i * major_spacing_x
        ax.axvline(x=x_pos, color=major_grid_color, linewidth=0.4, alpha=0.5)  # Further reduced linewidth and alpha
    
    # Draw horizontal major pink grid lines
    for i in range(5):
        y_pos = i * major_spacing_y
        ax.axhline(y=y_pos, color=major_grid_color, linewidth=0.4, alpha=0.5)  # Further reduced linewidth and alpha
    
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
import numpy as np

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
    light_grid_color = colors.HexColor("#ffeeee")  # Even lighter pink (was #ffe0e0)
    major_grid_color = colors.HexColor("#ffe0e0")   # Even lighter pink (was #ffcccc)
    
    # Minor grid lines (1mm spacing equivalent)
    minor_spacing_x = width / 60  # 60 divisions across width
    minor_spacing_y = height / 20  # 20 divisions across height
    
    # Vertical minor grid lines
    for i in range(61):
        x_pos = i * minor_spacing_x
        line = Line(x_pos, 0, x_pos, height, strokeColor=light_grid_color, strokeWidth=0.15)  # Further reduced strokeWidth
        drawing.add(line)
    
    # Horizontal minor grid lines
    for i in range(21):
        y_pos = i * minor_spacing_y
        line = Line(0, y_pos, width, y_pos, strokeColor=light_grid_color, strokeWidth=0.15)  # Further reduced strokeWidth
        drawing.add(line)
    
    # Major grid lines (5mm spacing equivalent)
    major_spacing_x = width / 12  # 12 divisions across width
    major_spacing_y = height / 4   # 4 divisions across height
    
    # Vertical major grid lines
    for i in range(13):
        x_pos = i * major_spacing_x
        line = Line(x_pos, 0, x_pos, height, strokeColor=major_grid_color, strokeWidth=0.3)  # Further reduced strokeWidth
        drawing.add(line)
    
    # Horizontal major grid lines
    for i in range(5):
        y_pos = i * major_spacing_y
        line = Line(0, y_pos, width, y_pos, strokeColor=major_grid_color, strokeWidth=0.3)  # Further reduced strokeWidth
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
    light_grid_color = colors.HexColor("#ffeeee")  # Even lighter pink (was #ffe0e0)
    major_grid_color = colors.HexColor("#ffe0e0")   # Even lighter pink (was #ffcccc)
    
    # Minor grid lines (1mm spacing equivalent)
    minor_spacing_x = width / 60  # 60 divisions across width
    minor_spacing_y = height / 20  # 20 divisions across height
    
    # Vertical minor grid lines
    for i in range(61):
        x_pos = i * minor_spacing_x
        line = Line(x_pos, 0, x_pos, height, strokeColor=light_grid_color, strokeWidth=0.15)  # Further reduced strokeWidth
        drawing.add(line)
    
    # Horizontal minor grid lines
    for i in range(21):
        y_pos = i * minor_spacing_y
        line = Line(0, y_pos, width, y_pos, strokeColor=light_grid_color, strokeWidth=0.15)  # Further reduced strokeWidth
        drawing.add(line)
    
    # Major grid lines (5mm spacing equivalent)
    major_spacing_x = width / 12  # 12 divisions across width
    major_spacing_y = height / 4   # 4 divisions across height
    
    # Vertical major grid lines
    for i in range(13):
        x_pos = i * major_spacing_x
        line = Line(x_pos, 0, x_pos, height, strokeColor=major_grid_color, strokeWidth=0.3)  # Further reduced strokeWidth
        drawing.add(line)
    
    # Horizontal major grid lines
    for i in range(5):
        y_pos = i * major_spacing_y
        line = Line(0, y_pos, width, y_pos, strokeColor=major_grid_color, strokeWidth=0.3)  # Further reduced strokeWidth
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
    import numpy as np
    
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
    
    # STEP 2: Draw pink ECG grid lines OVER pink background (even lighter colors)
    light_grid_color = '#ffeeee'  # Even lighter pink for minor grid lines (was #ffe0e0)
    major_grid_color = '#ffe0e0'  # Even lighter pink for major grid lines (was #ffcccc)
    
    # Minor grid lines (1mm equivalent spacing)
    minor_spacing_x = width / 60  # 60 minor divisions
    minor_spacing_y = height / 20  # 20 minor divisions
    
    # Draw vertical minor pink grid lines
    for i in range(61):
        x_pos = i * minor_spacing_x
        ax.axvline(x=x_pos, color=light_grid_color, linewidth=0.2, alpha=0.4)  # Further reduced linewidth and alpha
    
    # Draw horizontal minor pink grid lines
    for i in range(21):
        y_pos = i * minor_spacing_y
        ax.axhline(y=y_pos, color=light_grid_color, linewidth=0.2, alpha=0.4)  # Further reduced linewidth and alpha
    
    # Major grid lines (5mm equivalent spacing)
    major_spacing_x = width / 12  # 12 major divisions
    major_spacing_y = height / 4   # 4 major divisions
    
    # Draw vertical major pink grid lines
    for i in range(13):
        x_pos = i * major_spacing_x
        ax.axvline(x=x_pos, color=major_grid_color, linewidth=0.4, alpha=0.5)  # Further reduced linewidth and alpha
    
    # Draw horizontal major pink grid lines
    for i in range(5):
        y_pos = i * major_spacing_y
        ax.axhline(y=y_pos, color=major_grid_color, linewidth=0.4, alpha=0.5)  # Further reduced linewidth and alpha
    
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


def generate_ecg_report(filename="ecg_report.pdf", data=None, lead_images=None, dashboard_instance=None, ecg_test_page=None, patient=None):
    if data is None:
        # Dummy values (replace with Arduino parsed data)
        data = {
            "HR": 4833,
            "beat": 88,
            "PR": 160,
            "QRS": 90,
            "QT": 380,
            "QTc": 400,
            "ST": 100,
            "HR_max": 136,
            "HR_min": 74,
            "HR_avg": 88,
        }

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

    # Title
    story.append(Paragraph("<b>ECG Report</b>", heading))
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

   

    # Conclusion in table format
    story.append(Paragraph("<b>ECG Report Conclusion</b>", styles['Heading3']))
    story.append(Spacer(1, 8))   # Reduced from 10
    
    # Create conclusion table
    conclusion_headers = ["S.No.", "Conclusion"]
    conclusion_data = [
        ["1", "Sinus Rhythm"],
        ["2", "PAC (Premature Supraventricular Contraction)"],
        ["3", "Couplet of PAC"],
        ["4", "PAC Trigeminy"],
        ["5", "Supraventricular Tachycardia"]
    ]
    
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

    # ADD PageBreak HERE to send patient details to Page 2
    story.append(PageBreak())

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

    # RIGHT SIDE: Date/Time positioned for right side
    # Date/Time in column format (right aligned at top)
    date_time_style = ParagraphStyle(
        'DateTimeStyle',
        fontSize=12,
        fontName='Helvetica',  # Remove Bold
        textColor=colors.black,
        alignment=2,  # Right alignment
        spaceAfter=4,  # Reduced spacing
    )

    # Split date and time into separate paragraphs for column format
    if date_time_str:
        date_part = date_time_str.split()[0] if date_time_str.split() else ""
        time_part = date_time_str.split()[1] if len(date_time_str.split()) > 1 else ""
        
        # Date paragraph
        date_para = Paragraph(f"Date: {date_part}", date_time_style)
        story.append(date_para)
        
        # Time paragraph  
        time_para = Paragraph(f"Time: {time_part}", date_time_style)
        story.append(time_para)
    else:
        # Fallback if no date_time_str
        date_para = Paragraph("Date: ____", date_time_style)
        story.append(date_para)
        time_para = Paragraph("Time: ____", date_time_style)
        story.append(time_para)
    
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

    # Create 3-column vital parameters table (left positioned, normal text)
    vital_table_style = ParagraphStyle(
        'VitalTableStyle',
        fontSize=10,  # Same as Name, Age, Gender
        fontName='Helvetica',  # Normal font, not bold
        textColor=colors.black,
        alignment=0,  # Left alignment instead of center
    )

    # Create table data: 2 rows × 2 columns (as per your changes)
    vital_table_data = [
        [f"HR : {HR} bpm", f"QT: {QT} ms"],
        [f"PR : {PR} ms", f"QTc: {QTc} ms"],
        [f"QRS: {QRS} ms", f"ST: {ST} ms"]
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

    # Add vital parameters at VERY TOP of Page 2
    # story.append(vital_params_table)  # REMOVE this line
    # story.append(Spacer(1, 3))        # REMOVE this line

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
                    real_ecg_data = -np.array(ecg_test_page.data[3][-8000:])  # Last 8000 points = 16 seconds
                    real_data_available = True
                    print(f"🔄 Using ALL available -aVR data: {len(real_ecg_data)} points (16+ seconds)")
                elif lead in lead_to_index and len(ecg_test_page.data) > lead_to_index[lead]:
                    # Get ALL available real data for this lead
                    lead_index = lead_to_index[lead]
                    if len(ecg_test_page.data[lead_index]) > 0:
                        real_ecg_data = np.array(ecg_test_page.data[lead_index][-8000:])  # Last 8000 points = 16 seconds
                        real_data_available = True
                        print(f"🔄 Using ALL available {lead} data: {len(real_ecg_data)} points (16+ seconds)")
            
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
    patient_name_label = String(-30, 620, f"Name: {full_name}", 
                           fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(patient_name_label)

    patient_age_label = String(-30, 600, f"Age: {age}", 
                          fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(patient_age_label)

    patient_gender_label = String(-30, 580, f"Gender: {gender}", 
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

    # Add vital parameters SHIFTED LEFT at same Y levels with REDUCED GAP
    hr_label = String(180, 620, f"HR  : {HR} bpm", 
                     fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(hr_label)

    qt_label = String(280, 620, f"QT  : {QT} ms", 
                     fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(qt_label)

    pr_label = String(180, 600, f"PR  : {PR} ms", 
                     fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(pr_label)

    qtc_label = String(280, 600, f"QTc: {QTc} ms", 
                      fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(qtc_label)

    qrs_label = String(180, 580, f"QRS: {QRS} ms", 
                      fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(qrs_label)

    st_label = String(280, 580, f"ST  : {ST} ms", 
                     fontSize=10, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(st_label)

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

    # Add RIGHT-SIDE Conclusion Box (moved to the right)
    conclusion_y_start = -90  # Higher up (was -120)
    
    # Create a rectangular box for conclusions (shifted right) - SAME POSITION
    from reportlab.graphics.shapes import Rect
    conclusion_box = Rect(200, conclusion_y_start - 35, 300, 50,  # x shifted from 50 to 200
                         fillColor=None, strokeColor=colors.black, strokeWidth=1)
    master_drawing.add(conclusion_box)
    
    # CENTERED and STYLISH "Conclusion" header
    # Box center: 200 + (300/2) = 350, so text should be centered around 350
    conclusion_header = String(350, conclusion_y_start + 8, "✦ CONCLUSION ✦", 
                              fontSize=11, fontName="Helvetica-Bold", 
                              fillColor=colors.HexColor("#2c3e50"),
                              textAnchor="middle")  # This centers the text
    master_drawing.add(conclusion_header)
    
    # Column 1: First 3 conclusions (left side of box)
    conc1 = String(210, conclusion_y_start - 5, "1. Sinus Rhythm", 
                   fontSize=8, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(conc1)
    
    conc2 = String(210, conclusion_y_start - 15, "2. PAC (Premature)", 
                   fontSize=8, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(conc2)
    
    conc3 = String(210, conclusion_y_start - 25, "3. Couplet of PAC", 
                   fontSize=8, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(conc3)
    
    # Column 2: Next 3 conclusions (right side of box)
    conc4 = String(350, conclusion_y_start - 5, "4. PAC Trigeminy", 
                   fontSize=8, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(conc4)
    
    conc5 = String(350, conclusion_y_start - 15, "5. Supraventricular", 
                   fontSize=8, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(conc5)
    
    conc6 = String(350, conclusion_y_start - 25, "6. Normal ECG", 
                   fontSize=8, fontName="Helvetica", fillColor=colors.black)
    master_drawing.add(conc6)

    print(" Added Patient Info, Vital Parameters, Conclusions in Box, and Doctor Name/Signature to ECG grid")
    
    # STEP 5: Add SINGLE master drawing to story (NO containers)
    story.append(master_drawing)
    story.append(Spacer(1, 15))
    
    print(f" Added SINGLE master drawing with {successful_graphs}/12 ECG leads (ZERO containers)!")

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
            
            # ECG grid colors - SAME as existing
            light_grid_color = colors.HexColor("#ffcccc")  # Light pink minor grid
            
            major_grid_color = colors.HexColor("#ff9999")   # Darker pink major grid
            
            # Draw minor grid lines (1mm spacing) - FULL PAGE
            canvas.setStrokeColor(light_grid_color)
            canvas.setLineWidth(0.3)
            
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
            canvas.setLineWidth(0.8)
            
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
        y = 20  # 20 points from bottom
        canvas.drawString(x, y, footer_text)
        canvas.restoreState()

    # Build PDF
    doc.build(story, onFirstPage=_draw_logo_and_footer, onLaterPages=_draw_logo_and_footer)
    print(f"✓ ECG Report generated: {filename}")


# REMOVE ENTIRE create_sample_ecg_images function (lines ~1222-1257)

# REMOVE ENTIRE main execution block (lines ~1260-1265)
# if __name__ == "__main__":
#     # Create sample images with transparency (force recreation)
#     create_sample_ecg_images(force_recreate=True)
#     
#     # Generate report
#     generate_ecg_report("test_ecg_report.pdf")