import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics import renderPDF

# Try to import svglib, handle if missing
try:
    from svglib.svglib import svg2rlg
except ImportError:
    svg2rlg = None

OUTPUT_DIR = "generated_docs"
ASSETS_DIR = "src/assets"
LOGO_PATH_PNG = os.path.join(ASSETS_DIR, "logo.png")
LOGO_PATH_SVG = os.path.join(ASSETS_DIR, "logo.svg")

def create_experience_letter(employee_data: dict):
    """
    Generates an Experience Letter PDF for the given employee.
    Branded for Keymouse IT.
    """
    # Ensure directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    filename = f"Experience_Letter_{employee_data.get('name', 'Employee').replace(' ', '_')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        alignment=1, # Center
        spaceAfter=20
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        alignment=1, # Center
        fontSize=10,
        textColor="gray"
    )

    normal_style = styles['Normal']
    normal_style.fontSize = 12
    normal_style.leading = 14
    
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        fontName='Helvetica-Bold'
    )

    story = []

    # 1. Logo Logic (SVG Priority -> PNG Fallback)
    logo_added = False
    
    # Try SVG
    if os.path.exists(LOGO_PATH_SVG) and svg2rlg:
        try:
            drawing = svg2rlg(LOGO_PATH_SVG)
            
            # Smart Scaling
            desired_width = 2.5 * inch
            scaling_factor = desired_width / drawing.width
            
            drawing.width = drawing.width * scaling_factor
            drawing.height = drawing.height * scaling_factor
            drawing.scale(scaling_factor, scaling_factor)
            
            # Using logic to center requires a wrapper or alignment
            # ReportLab Drawings in Platypus are a bit tricky to center directly via hAlign
            # But we can assume left alignment is okay, or wrap in a table
            
            story.append(drawing)
            story.append(Spacer(1, 12))
            logo_added = True
        except Exception as e:
            print(f"Error loading SVG logo: {e}")

    # Fallback to PNG if SVG failed or missing
    if not logo_added and os.path.exists(LOGO_PATH_PNG):
        try:
            im = Image(LOGO_PATH_PNG, width=2*inch, height=0.75*inch)
            im.hAlign = 'LEFT' 
            story.append(im)
            story.append(Spacer(1, 12))
        except Exception as e:
            print(f"Error loading PNG logo: {e}")

    # 2. Company Header
    story.append(Paragraph("<b>Keymouse IT</b>", header_style))
    story.append(Paragraph("Start Hub, Next57, Chandigarh", header_style))
    story.append(Spacer(1, 36))

    # 3. Date
    story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
    story.append(Spacer(1, 24))

    # 4. Title
    story.append(Paragraph("TO WHOM IT MAY CONCERN", title_style))
    story.append(Spacer(1, 12))

    # 5. Content
    name = employee_data.get('name', 'Unknown Name')
    role = employee_data.get('role', 'Employee')
    dept = employee_data.get('department', 'General')
    start_date = employee_data.get('joining_date', 'their joining date')

    content = f"""
    This is to certify that <b>{name}</b> has been working with <b>Keymouse IT</b> 
    as a <b>{role}</b> in the <b>{dept}</b> department since {start_date}.
    <br/><br/>
    During their tenure with us, we have found them to be sincere, hardworking, and distinctively 
    resourceful. They have maintained a good character and we wish them all the best for their 
    future endeavors.
    """
    
    story.append(Paragraph(content, normal_style))
    story.append(Spacer(1, 48))

    # 6. Signatory
    story.append(Paragraph("Sincerely,", normal_style))
    story.append(Spacer(1, 48))
    story.append(Paragraph("Authorized Signatory", signature_style))
    story.append(Paragraph("HR Department", normal_style))
    story.append(Paragraph("Keymouse IT", normal_style))

    # Build PDF
    doc.build(story)
    
    return filename, filepath
