"""
PDF Generator for MirAI School of Technology (SoT) Policy Handbook 2026.
Creates a complete, structured, multi-page PDF handbook if one is not already present.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 750, 558, 750)
        self.drawString(54, 755, "MirAI School of Technology — Official Student Policy Handbook (Academic Year 2026)")
        
        # Footer
        self.line(54, 50, 558, 50)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_text)
        self.drawString(54, 38, "CONFIDENTIAL & PROPRIETARY — ACADEMIC POLICIES DIVISION")
        self.restoreState()


def generate_handbook_pdf(output_path: str = "data/Mirai_SoT_Policy_Handbook_2026.pdf") -> str:
    """Generates the official Mirai SoT Policy Handbook PDF."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(output_path):
        return output_path

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1E293B"),
        alignment=1,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=25
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    story = []

    # Title Banner
    story.append(Spacer(1, 20))
    story.append(Paragraph("MIRAI SCHOOL OF TECHNOLOGY (SoT)", title_style))
    story.append(Paragraph("OFFICIAL STUDENT POLICY HANDBOOK & CODE OF CONDUCT<br/><b>Academic Year 2026 – 2027</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=15))

    # Document Metadata Box
    meta_data = [
        [Paragraph("<b>Document Version:</b> 4.2 (Final)", body_style), Paragraph("<b>Effective Date:</b> January 1, 2026", body_style)],
        [Paragraph("<b>Approved By:</b> Academic Senate & Dean of SoT", body_style), Paragraph("<b>Jurisdiction:</b> All B.Tech & M.Tech Programs", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[250, 250])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # SECTION 1
    story.append(Paragraph("SECTION 1: ACADEMIC REGULATIONS & CREDIT STRUCTURE", h1_style))
    story.append(Paragraph("<b>1.1 Minimum & Maximum Credit Requirements:</b>", body_style))
    story.append(Paragraph("• Every full-time undergraduate student in the School of Technology must register for a minimum of <b>20 credits</b> and a maximum of <b>26 credits</b> in any regular semester.", bullet_style))
    story.append(Paragraph("• Total cumulative credits required to graduate with a Bachelor of Technology (B.Tech) degree is strictly <b>160 credits</b>.", bullet_style))
    story.append(Paragraph("• Fast-track graduation is permitted for high-performing students who have maintained a CGPA of 9.0 or above across their first four semesters, allowing a maximum overload of 28 credits per semester upon Academic Advisor approval.", bullet_style))
    story.append(Paragraph("<b>1.2 Course Add/Drop Period:</b>", body_style))
    story.append(Paragraph("• Students may add or drop elective courses within the first <b>10 academic working days</b> of the semester without penalty or record on their transcript.", bullet_style))
    story.append(Spacer(1, 10))

    # SECTION 2
    story.append(Paragraph("SECTION 2: ATTENDANCE MANDATE & MEDICAL CONDONATION", h1_style))
    story.append(Paragraph("<b>2.1 Mandatory Minimum Attendance:</b>", body_style))
    story.append(Paragraph("• All enrolled students must maintain a minimum of <b>85% aggregate attendance</b> in each registered course (both lecture and laboratory components).", bullet_style))
    story.append(Paragraph("<b>2.2 Condonation for Medical Emergency:</b>", body_style))
    story.append(Paragraph("• Students with attendance between <b>75% and 84.9%</b> may apply for attendance condonation strictly on verified medical grounds or bereavement.", bullet_style))
    story.append(Paragraph("• To qualify for condonation, a formal Medical Certificate issued by a registered medical practitioner along with the hospital admission/discharge record must be submitted to the Office of the Dean of Student Affairs within <b>3 working days</b> of resuming classes.", bullet_style))
    story.append(Paragraph("<b>2.3 Failure to Meet Minimum Attendance (Non-Eligible / NS Grade):</b>", body_style))
    story.append(Paragraph("• Any student whose final aggregate attendance falls <b>below 75%</b> under any circumstance is automatically barred from sitting for the End-Semester Examination (ESE) and is awarded a Non-Satisfactory <b>'NS' grade</b>.", bullet_style))
    story.append(Paragraph("• A course with an 'NS' grade cannot be cleared via supplementary examinations; the student must repeat the entire course during the subsequent Summer Semester or regular semester.", bullet_style))
    story.append(Spacer(1, 10))

    # SECTION 3
    story.append(Paragraph("SECTION 3: GRADING SCHEME & CGPA CALCULATION", h1_style))
    story.append(Paragraph("<b>3.1 10-Point Absolute & Relative Grading Scale:</b>", body_style))
    
    grade_data = [
        ["Letter Grade", "Grade Point", "Performance Level", "Marks Range (Indicative)"],
        ["O", "10.0", "Outstanding", ">= 90%"],
        ["A+", "9.0", "Excellent", "80% – 89%"],
        ["A", "8.0", "Very Good", "70% – 79%"],
        ["B+", "7.0", "Good", "60% – 69%"],
        ["B", "6.0", "Above Average", "50% – 59%"],
        ["C", "5.0", "Pass / Average", "40% – 49%"],
        ["F", "0.0", "Fail (Requires Re-exam)", "< 40%"],
        ["NS", "0.0", "Attendance Shortage (Course Repeat)", "Attendance < 75%"]
    ]
    grade_table = Table(grade_data, colWidths=[80, 75, 180, 165])
    grade_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('ALIGN', (0,0), (1,-1), 'CENTER'),
    ]))
    story.append(grade_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>3.2 Academic Probation & Minimum CGPA:</b>", body_style))
    story.append(Paragraph("• Students must maintain a minimum cumulative CGPA of <b>5.00</b> to remain in good standing.", bullet_style))
    story.append(Paragraph("• If a student's CGPA drops below 5.00 at the end of an academic semester, they will be placed on <b>Academic Probation</b> for the following term.", bullet_style))
    
    story.append(PageBreak())

    # SECTION 4
    story.append(Paragraph("SECTION 4: ACADEMIC INTEGRITY & GENERATIVE AI USAGE POLICY", h1_style))
    story.append(Paragraph("<b>4.1 Academic Dishonesty & Plagiarism Thresholds:</b>", body_style))
    story.append(Paragraph("• All submitted coursework, laboratory assignments, capstone reports, and dissertation manuscripts are screened using standard plagiarism detection software.", bullet_style))
    story.append(Paragraph("• <b>Similarity Index < 10%:</b> Acceptable threshold for normal academic citation.", bullet_style))
    story.append(Paragraph("• <b>Similarity Index 10% to 25%:</b> Flagged for review; student receives a mandatory resubmission requirement with a capped maximum grade of 'B+'.", bullet_style))
    story.append(Paragraph("• <b>Similarity Index > 25%:</b> Direct referral to the School Disciplinary Committee (SDC). Results in an automatic 'F' grade in the assignment and disciplinary reprimand on record.", bullet_style))
    story.append(Paragraph("<b>4.2 Generative AI and Code Generation Tools:</b>", body_style))
    story.append(Paragraph("• Generative AI tools (including LLMs, code copilots, and AI paraphrasers) may be utilized for brainstorming and exploratory learning only if explicitly permitted by the course instructor.", bullet_style))
    story.append(Paragraph("• Using Generative AI during timed lab evaluations, mid-term tests, or final examinations constitutes severe academic malpractice. Any violation leads to immediate cancellation of the exam paper and an 'F' grade for the course.", bullet_style))
    story.append(Spacer(1, 10))

    # SECTION 5
    story.append(Paragraph("SECTION 5: HACKATHONS, COMPETITIONS & DUTY LEAVE (OD)", h1_style))
    story.append(Paragraph("<b>5.1 On-Duty (OD) Leave Quota for Hackathons & Conferences:</b>", body_style))
    story.append(Paragraph("• Students selected to represent MirAI School of Technology at national or international hackathons, coding contests, or peer-reviewed research conferences are eligible for On-Duty (OD) attendance credit.", bullet_style))
    story.append(Paragraph("• The maximum allowable OD quota is <b>5 working days per semester</b>.", bullet_style))
    story.append(Paragraph("• OD approval requires prior written recommendation from the Faculty Sponsor and submission of the official invitation letter to the Head of Department (HOD) at least <b>5 business days prior</b> to the event date. Post-facto OD claims are strictly rejected.", bullet_style))
    story.append(Paragraph("<b>5.2 Eighth-Semester Industry Internship Policy:</b>", body_style))
    story.append(Paragraph("• Students seeking full-semester off-campus industry internships during their 8th semester must have a <b>minimum CGPA of 7.50</b> with <b>zero active backlogs</b> at the time of application.", bullet_style))
    story.append(Paragraph("• The recruiting organization must provide a signed corporate internship offer letter offering a minimum stipend of ₹20,000 per month.", bullet_style))
    story.append(Spacer(1, 10))

    # SECTION 6
    story.append(Paragraph("SECTION 6: HOSTEL REGULATIONS & RESIDENTIAL CODE", h1_style))
    story.append(Paragraph("<b>6.1 Campus and Hostel In-Times:</b>", body_style))
    story.append(Paragraph("• <b>Weekday Curfew (Monday to Friday):</b> All hostel residents must mark their biometric attendance at the hostel security gate by <b>9:30 PM</b>.", bullet_style))
    story.append(Paragraph("• <b>Weekend Curfew (Saturday and Sunday):</b> Hostel entry is permitted up to <b>10:30 PM</b>.", bullet_style))
    story.append(Paragraph("• Late entries without prior approved ERP gate pass will incur a penalty of ₹500 for the first offense and ₹1,500 with parental notification for subsequent infractions.", bullet_style))
    story.append(Paragraph("<b>6.2 Night Out & Leave Passes:</b>", body_style))
    story.append(Paragraph("• Overnight leave requires submission of an online request on the MirAI Student ERP portal at least <b>24 hours in advance</b>, verified via automated SMS/email OTP consent from the registered parent/guardian.", bullet_style))
    story.append(Paragraph("<b>6.3 Quiet Hours & Safety:</b>", body_style))
    story.append(Paragraph("• Mandatory quiet hours are observed between <b>11:00 PM and 6:00 AM</b> daily. High-volume audio systems and loud gatherings in corridor areas are strictly prohibited.", bullet_style))
    story.append(Spacer(1, 10))

    # SECTION 7
    story.append(Paragraph("SECTION 7: SCHOLARSHIP RETENTION & FEE REFUND POLICY", h1_style))
    story.append(Paragraph("<b>7.1 Merit Scholarship Renewal Rules:</b>", body_style))
    story.append(Paragraph("• Students awarded the MirAI Merit Scholarship must maintain a minimum cumulative CGPA of <b>8.50</b> at the end of each academic year.", bullet_style))
    story.append(Paragraph("• The student must have <b>zero active backlogs</b> and no disciplinary sanctions from the Proctorial Board. Failure to meet the 8.50 CGPA threshold results in immediate revocation of the scholarship for all subsequent semesters.", bullet_style))
    story.append(Paragraph("<b>7.2 Fee Refund Schedule for Voluntary Withdrawal:</b>", body_style))
    
    refund_data = [
        ["Withdrawal Notice Received", "Tuition Fee Refund %", "Hostel / Mess Fee Refund"],
        ["15 or more days before commencement of classes", "100% (minus ₹1,000 processing fee)", "100% full refund"],
        ["Less than 15 days before commencement", "90% of total tuition fee", "Pro-rata monthly basis"],
        ["Within 15 days after commencement of classes", "80% of total tuition fee", "Pro-rata monthly basis"],
        ["Between 16 and 30 days after commencement", "50% of total tuition fee", "Pro-rata mess fee only"],
        ["More than 30 days after commencement", "0% (No tuition fee refund)", "Pro-rata mess fee only"]
    ]
    refund_table = Table(refund_data, colWidths=[200, 160, 140])
    refund_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ]))
    story.append(refund_table)
    story.append(Spacer(1, 10))

    # SECTION 8
    story.append(Paragraph("SECTION 8: GRIEVANCE REDRESSAL & OMBUDSMAN", h1_style))
    story.append(Paragraph("<b>8.1 Grievance Escalation Hierarchy:</b>", body_style))
    story.append(Paragraph("• <b>Level 1 (Faculty Advisor / Mentor):</b> Initial review and informal resolution within 3 working days.", bullet_style))
    story.append(Paragraph("• <b>Level 2 (Head of Department):</b> Formal review within 7 working days if unresolved at Level 1.", bullet_style))
    story.append(Paragraph("• <b>Level 3 (University Ombudsman / Internal Complaints Committee):</b> Final administrative appeal. The Ombudsman shall conduct a hearing and deliver a binding written resolution within <b>14 business days</b> of receipt of the formal petition.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path

if __name__ == "__main__":
    out = generate_handbook_pdf()
    print(f"Generated handbook at: {out}")
