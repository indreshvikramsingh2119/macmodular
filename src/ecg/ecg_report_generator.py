from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, PageBreak
)
import os


def capture_real_ecg_graphs_from_dashboard(dashboard_instance=None, ecg_test_page=None):
    """
    Capture real ECG graphs from dashboard/twelve_lead_test
    Returns: dict with lead image paths
    """
    lead_img_paths = {}
    
    # Get current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    project_root = os.path.abspath(project_root)
    
    print(" Capturing real ECG graphs from dashboard...")
    
    # Method 1: Get from ECGTestPage (twelve_lead_test.py)
    if ecg_test_page and hasattr(ecg_test_page, 'figures'):
        print(" Found ECGTestPage with figures")
        ordered_leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        
        for i, lead in enumerate(ordered_leads):
            try:
                # Get figure from ECGTestPage
                if i < len(ecg_test_page.figures):
                    fig = ecg_test_page.figures[i]
                    
                    # Save to project root directory
                    img_path = os.path.join(project_root, f"lead_{lead}.png")
                    fig.savefig(img_path, 
                              bbox_inches='tight',     # Remove extra space
                              pad_inches=0.05,         # Minimal padding
                              dpi=200,                 # High resolution for print
                              facecolor='none',        # TRANSPARENT background
                              edgecolor='none',        # No border
                              transparent=True)        # ENABLE transparency
                    lead_img_paths[lead] = img_path
                    
                    print(f" Captured Lead {lead}: {img_path}")
                    
            except Exception as e:
                print(f" Error capturing Lead {lead}: {e}")
    
    # Method 2: Get from ECGTestPage canvases
    elif ecg_test_page and hasattr(ecg_test_page, 'canvases'):
        print(" Found ECGTestPage with canvases")
        ordered_leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        
        for i, lead in enumerate(ordered_leads):
            try:
                if i < len(ecg_test_page.canvases):
                    canvas = ecg_test_page.canvases[i]
                    fig = canvas.figure
                    
                    # Save to project root directory
                    img_path = os.path.join(project_root, f"lead_{lead}.png")
                    fig.savefig(img_path, 
                              bbox_inches='tight',
                              pad_inches=0.05,
                              dpi=200,
                              facecolor='none',        # TRANSPARENT background
                              edgecolor='none',
                              transparent=True)        # ENABLE transparency
                    lead_img_paths[lead] = img_path
                    
                    print(f" Captured Lead {lead}: {img_path}")
                    
            except Exception as e:
                print(f"Error capturing Lead {lead}: {e}")
    
    # Method 3: Get from Lead12BlackPage (recording.py)
    elif dashboard_instance and hasattr(dashboard_instance, 'lead12_page'):
        print(" Found Lead12BlackPage")
        lead12_page = dashboard_instance.lead12_page
        
        if hasattr(lead12_page, 'canvases') and hasattr(lead12_page, 'lead_names'):
            for i, lead in enumerate(lead12_page.lead_names):
                try:
                    if i < len(lead12_page.canvases):
                        canvas = lead12_page.canvases[i]
                        fig = canvas.figure
                        
                        # Save to project root directory
                        img_path = os.path.join(project_root, f"lead_{lead}.png")
                        fig.savefig(img_path, 
                                  bbox_inches='tight',
                                  pad_inches=0.05,
                                  dpi=200,
                                  facecolor='none',        # TRANSPARENT background
                                  edgecolor='none',
                                  transparent=True)        # ENABLE transparency
                        lead_img_paths[lead] = img_path
                        
                        print(f"Captured Lead {lead}: {img_path}")
                        
                except Exception as e:
                    print(f" Error capturing Lead {lead}: {e}")
    
    # Method 4: Try to find active ECG figures globally
    else:
        print("earching for active ECG figures...")
        try:
            import matplotlib.pyplot as plt
            
            # Get all open figures
            figs = [plt.figure(i) for i in plt.get_fignums()]
            
            if len(figs) >= 12:
                ordered_leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
                
                for i, lead in enumerate(ordered_leads):
                    if i < len(figs):
                        fig = figs[i]
                        
                        # Save to project root directory
                        img_path = os.path.join(project_root, f"lead_{lead}.png")
                        fig.savefig(img_path, 
                                  bbox_inches='tight',
                                  pad_inches=0.05,
                                  dpi=200,
                                  facecolor='none',        
                                  edgecolor='none',
                                  transparent=True)       
                        lead_img_paths[lead] = img_path
                        
                        print(f" Captured Lead {lead}: {img_path}")
            else:
                print(f"  Only found {len(figs)} figures, need 12 for all leads")
                
        except Exception as e:
            print(f" Error searching for figures: {e}")
    
    if lead_img_paths:
        print(f" Successfully captured {len(lead_img_paths)}/12 real ECG graphs!")
    else:
        print(" No real ECG graphs found. Using fallback...")
        # Fallback: try to read from existing files
        ordered_leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        for lead in ordered_leads:
            img_path = os.path.join(project_root, f"lead_{lead}.png")
            if os.path.exists(img_path):
                lead_img_paths[lead] = img_path
                print(f" Found existing Lead {lead}: {img_path}")
    
    return lead_img_paths


def generate_ecg_report(filename="ecg_report.pdf", data=None, lead_images=None, dashboard_instance=None, ecg_test_page=None):
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

    # UPDATED: Get real ECG graphs from dashboard instead of sample images
    if lead_images is None:
        print(" Attempting to capture real ECG graphs from dashboard...")
        lead_images = capture_real_ecg_graphs_from_dashboard(dashboard_instance, ecg_test_page)
        
        # If no real graphs found, show error
        if not lead_images:
            print(" No real ECG graphs available!")
            print("Please make sure:")
            print("   1. ECG test is running on dashboard")
            print("   2. 12-lead graphs are currently displayed")
            print("   3. Try generating PDF while ECG is active")
            return "Error: No real ECG graphs found"

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

    # Report Overview
    story.append(Paragraph("<b>Report Overview</b>", styles['Heading3']))
    overview_data = [
        ["Total Number of Heartbeats (beats):", data["HR"]],
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
    story.append(Spacer(1, 35))

    # Observation with 3 parts in ONE table (like in the image)
    story.append(Paragraph("<b>OBSERVATION</b>", styles['Heading3']))
    story.append(Spacer(1, 10))
    
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
    ROW_HEIGHT = 25       
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
        ("BOTTOMPADDING", (0, 1), (-1, -1), ROW_HEIGHT//2),
        ("TOPPADDING", (0, 1), (-1, -1), ROW_HEIGHT//2),
        
        # Grid and borders
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(obs_table)
    story.append(Spacer(1, 18))

    story.append(PageBreak())

    # Supraventricular Rhythm
    story.append(Paragraph("<b>Supraventricular Rhythm</b>", styles['Heading3']))
    supra_data = [
        ["Total Number of Supraventricular Heart Beats:", "362"],
        ["Number of PAC:", "340"],
        ["Couplet of PAC:", "3"],
        ["Supraventricular Bigeminy:", "0"],
        ["Supraventricular Trigeminy:", "19"],
        ["Supraventricular Tachycardia:", "3"],
        ["Maximum Duration of Tachycardia (s):", "2.00"],
    ]
    supra_table = Table(supra_data, colWidths=[350, 150])
    supra_table.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(supra_table)
    story.append(Spacer(1, 18))

    # Ventricular Rhythm
    story.append(Paragraph("<b>Ventricular Rhythm</b>", styles['Heading3']))
    vent_data = [
        ["Total Number of Ventricular Heart Beats:", "0"],
        ["Number of PVC:", "0"],
        ["Couplet of PVC:", "0"],
        ["Ventricular Bigeminy:", "0"],
        ["Ventricular Trigeminy:", "0"],
        ["Ventricular Tachycardia:", "0"],
    ]
    vent_table = Table(vent_data, colWidths=[350, 150])
    vent_table.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(vent_table)
    story.append(Spacer(1, 18))

    # Conclusion in table format
    story.append(Paragraph("<b>ECG Report Conclusion</b>", styles['Heading3']))
    story.append(Spacer(1, 10))
    
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
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
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
    story.append(Spacer(1, 18))

    # Notes
    story.append(Paragraph("<b>Note:</b>", styles['Heading3']))
    story.append(Paragraph("1. Due to sporadic nature of ECG events, each result may differ.", styles['Normal']))
    story.append(Paragraph("2. Results are for reference only, not for clinical diagnosis.", styles['Normal']))
    story.append(PageBreak())

    #
    # STEP 1: Add this specific ECG grid pattern as full page background
    # Create ECG grid pattern programmatically (exactly like your image)
    from reportlab.graphics.shapes import Drawing, Group, Line, Rect
    from reportlab.lib.units import mm

    def create_ecg_grid_background():
        """Create the exact ECG grid pattern from your image"""
        # A4 page dimensions
        width = 520  # A4 width in points (adjusted for margins)
        height = 760  # A4 height in points (adjusted for margins)
        
        drawing = Drawing(width, height)
        
        # ECG grid colors (pink/red like medical ECG paper)
        light_grid_color = colors.HexColor("#ffcccc")  # Light pink for minor grid
        major_grid_color = colors.HexColor("#ff9999")  # Darker pink for major grid
        
        # Create background rectangle
        bg_rect = Rect(0, 0, width, height, fillColor=colors.HexColor("#ffe6e6"), strokeColor=None)
        drawing.add(bg_rect)
        
        # Minor grid lines (1mm spacing)
        minor_spacing = 1 * mm
        
        # Vertical minor grid lines
        x = 0
        while x <= width:
            line = Line(x, 0, x, height, strokeColor=light_grid_color, strokeWidth=0.3)
            drawing.add(line)
            x += minor_spacing
        
        # Horizontal minor grid lines  
        y = 0
        while y <= height:
            line = Line(0, y, width, y, strokeColor=light_grid_color, strokeWidth=0.3)
            drawing.add(line)
            y += minor_spacing
        
        # Major grid lines (5mm spacing) - thicker and darker
        major_spacing = 5 * mm
        
        # Vertical major grid lines
        x = 0
        while x <= width:
            line = Line(x, 0, x, height, strokeColor=major_grid_color, strokeWidth=0.8)
            drawing.add(line)
            x += major_spacing
        
        # Horizontal major grid lines
        y = 0  
        while y <= height:
            line = Line(0, y, width, y, strokeColor=major_grid_color, strokeWidth=0.8)
            drawing.add(line)
            y += major_spacing
        
        return drawing

    # Add the ECG grid background to page 3
    ecg_grid_bg = create_ecg_grid_background()
    story.append(ecg_grid_bg)

    # Move content back to top to overlay on background
    story.append(Spacer(1, -740))

    print(" Added custom ECG grid background pattern to Page 3")


    title_style = ParagraphStyle(
        'ECGTitle',
        fontSize=18,
        textColor=colors.HexColor("#000000"),
        spaceAfter=15,
        alignment=1,  # center
        bold=True
    )
    story.append(Paragraph("<b>12-Lead Electrocardiogram</b>", title_style))

    # Vital Parameters Header (completely transparent)
    vital_style = ParagraphStyle(
        'VitalStyle',
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=15,
        alignment=1  # center
        # No backColor - completely transparent
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

    vital_header = f"HR: {HR} bpm    PR: {PR} ms    QRS: {QRS} ms    QT: {QT} ms    QTc: {QTc} ms    ST: {ST} ms"
    story.append(Paragraph(vital_header, vital_style))
    story.append(Spacer(1, 15))

    # VERTICAL ECG STRIPS LAYOUT (12 strips vertically over grid background)
    lead_order = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
    successful_graphs = 0

    print(" Creating 12 vertical ECG strips over grid background...")

    # Create all 12 vertical strips
    all_strips_data = []

    for lead in lead_order:
        if lead in lead_images and os.path.exists(lead_images[lead]):
            try:
                # Lead label (NO background - completely transparent)
                lead_label = Paragraph(
                    f"<b>{lead}</b>", 
                    ParagraphStyle(
                        'VerticalLeadStyle',
                        fontSize=10,
                        fontName='Helvetica-Bold',
                        textColor=colors.black,
                        alignment=0,  # left
                        spaceAfter=0,
                        leftIndent=10
                        # backColor COMPLETELY REMOVED
                    )
                )
                
                # ECG strip image (full width for vertical layout)
                strip_img = Image(lead_images[lead], width=460, height=45)
                
                # Create row with label and strip
                strip_row = [lead_label, strip_img]
                all_strips_data.append(strip_row)
                
                successful_graphs += 1
                print(f" Added vertical strip for Lead {lead} ({successful_graphs}/12)")
                
            except Exception as e:
                print(f" Error with Lead {lead}: {e}")
                error_row = [
                    Paragraph(f"<b>{lead}</b>",      # Remove "Lead" word too
                             ParagraphStyle('ErrorStyle')),  # No backColor
                    Paragraph("Error loading", 
                             ParagraphStyle('ErrorStyle'))   # No backColor
                ]
                all_strips_data.append(error_row)
        else:
            print(f" Missing Lead {lead}")
            missing_row = [
                Paragraph(f"<b>{lead}</b>",          # Remove "Lead" word too
                         ParagraphStyle('MissingStyle')),  # No backColor
                Paragraph("Not available", 
                         ParagraphStyle('MissingStyle'))   # No backColor
            ]
            all_strips_data.append(missing_row)

    # Create single vertical table with all 12 strips (transparent to show grid)
    vertical_strips_table = Table(all_strips_data, colWidths=[60, 460], rowHeights=[50] * len(all_strips_data))

    # Style the vertical strips table (transparent to show ECG grid)
    vertical_strips_table.setStyle(TableStyle([
        # NO background color - let grid show through
        # ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffe6e6")),  # REMOVED
        
        # Subtle borders only
        ("LINEBELOW", (0, 0), (-1, -1), 0.2, colors.HexColor("#ff999950")),  # Very light lines
        
        # Cell alignment
        ("ALIGN", (0, 0), (0, -1), "LEFT"),     # Lead labels left aligned
        ("ALIGN", (1, 0), (1, -1), "CENTER"),   # Strips centered
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), # All content middle aligned
        
        # Minimal padding
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(vertical_strips_table)
    story.append(Spacer(1, 15))

    print(f" 12 vertical ECG strips over custom grid background: {successful_graphs}/12 leads")

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

    # Build PDF
    doc.build(story)
    print(f"✓ ECG Report generated: {filename}")


# BONUS: Add a function to create sample ECG images for testing
def create_sample_ecg_images():
    """Create sample ECG images for testing if they don't exist"""
    import matplotlib.pyplot as plt
    import numpy as np
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    project_root = os.path.abspath(project_root)
    
    leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
    
    for lead in leads:
        img_path = os.path.join(project_root, f"lead_{lead}.png")
        
        if not os.path.exists(img_path):
            # Create a simple ECG-like waveform
            fig, ax = plt.subplots(figsize=(6, 2))
            t = np.linspace(0, 2, 1000)
            
            # Generate ECG-like signal
            ecg_signal = np.sin(2 * np.pi * 1.2 * t) + 0.5 * np.sin(2 * np.pi * 5 * t)
            # Add some spikes for R waves
            for i in range(2):
                spike_pos = 0.5 + i * 1.0
                spike_indices = np.where((t >= spike_pos - 0.05) & (t <= spike_pos + 0.05))
                ecg_signal[spike_indices] += 2 * np.exp(-((t[spike_indices] - spike_pos) / 0.02) ** 2)
            
            ax.plot(t, ecg_signal, 'b-', linewidth=1.5)
            ax.set_title(f"Lead {lead}")
            ax.set_ylim(-2, 4)
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('white')
            
            fig.savefig(img_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            print(f"Created sample image: {img_path}")


if __name__ == "__main__":
    # Create sample images if they don't exist
    create_sample_ecg_images()
    
    # Generate report
    generate_ecg_report("test_ecg_report.pdf")