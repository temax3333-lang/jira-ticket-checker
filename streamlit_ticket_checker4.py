import streamlit as st
from groq import Groq
import pandas as pd
from datetime import datetime
import re
import os

# Page configuration
st.set_page_config(
    page_title="Atlas-Toppan Ticket Checker",
    page_icon="🔵",
    layout="wide"
)

# Initialize session state for template population
if 'template_summary' not in st.session_state:
    st.session_state.template_summary = ""
if 'template_description' not in st.session_state:
    st.session_state.template_description = ""

# Initialize Groq client
@st.cache_resource
def get_client():
    return Groq(api_key=os.environ.get("GROQ_API_KEY"))

client = get_client()

# ============================================
# YOUR EXACT WORKFLOW FROM THE TABLE
# ============================================
WORKFLOW_MAPPING = {
    1: "INITIATE - CUSTOMER",
    2: "PAYMENT - flayget",
    3: "VERIFICATION - OFFICER",
    4: "BIOMETRIC - OFFICER",
    5: "LEGACY_VALID - VALIDATION",
    6: "LEGACY_ADJUD - ADJUDICATION",
    7: "ABIS_VALID - VALIDATION",
    8: "MANUAL_ADJUD - ADJUDICATION",
    9: "WATCHLIST - VALIDATION",
    10: "WATCHLIST_ADJUD - ADJUDICATION",
    11: "AUTHORIZE - OFFICER",
    12: "ORDERED - Backend",
    13: "PERSO - PERSO",
    14: "PRODUCED - OTHER",
    15: "RECEIVED - OTHER",
    16: "ISSUED - OTHER",
    17: "COMPLETED - OTHER"
}

# Rule for tickets
VALIDATION_STEPS = [5, 7, 9]
ADJUDICATION_STEPS = [6, 8, 10]

# Good ticket examples from your data
GOOD_TICKET_EXAMPLES = [
    {
        "summary": " URGENT - EXPIRED TO LOST",
        "description": "ACPP52500B25A4P\n\nThis ARN was requested to have a change from EXPIRED TO LOST,\n\nPlease make the necessary change and have it SYNCED to KALITY, to ensure proper work flow.\n\nAttachment: WhatsApp Image.jpeg",
        "why": "Single ARN, clear before/after, specific location, attachment"
    },
    {
        "summary": " Urgent - Application type change",
        "description": "AAPP4260C222B6P\n\nThe application was initiated as Ordinary Passport. Please update it to Reissue – Document Expired\n\nAttachment: WhatsApp Image.jpeg",
        "why": "Single ARN, current status, specific change, reason provided"
    },
    {
        "summary": "URGENT - REJECTED FROM PERSO (large)",
        "description": "AAPP4260C07777P\n\nThis was rejected from PERSO because of - \"Applicant's photo is too large\",\n\nPlease Resize the photo to complete the proper workflow.",
        "why": "Single ARN, exact error message, clear action"
    }
]

# Bad ticket examples
BAD_TICKET_EXAMPLES = [
    {
        "summary": "legacy stuck",
        "description": "ACPP52500E3408P\nACPP525004E251P\nACPP5250047AE3P\nACPP5250056762P\nACPP5250063A30P\nACPP52500564F6P\nACPP5260232559P\nACPP52500D97B3P\nACPP52500EBC30P\nACPP5250058029P\n\nStuck at Legacy Data Validation\n\nPlease transfer it to the appropriate workflow.",
        "why": "> 10 ARNs in one ticket, generic description, no specific action"
    }
]

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #FFFFFF;
        background: linear-gradient(90deg, #0E1117, #1E1E1E);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        border-left: 5px solid #FF4B4B;
    }
    .feedback-box {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 5px solid #FF4B4B;
        margin-top: 1rem;
    }
    .validation-box {
        background-color: #1E3A5F;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2196F3;
        margin: 1rem 0;
    }
    .adjudication-box {
        background-color: #1E4A3F;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    .stats-card {
        background: linear-gradient(135deg, #262730, #1E1E1E);
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        border: 1px solid #FF4B4B;
    }
    .rule-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .validation-badge {
        background-color: #2196F3;
        color: white;
    }
    .adjudication-badge {
        background-color: #4CAF50;
        color: white;
    }
    /* Reduce spacing in feedback box */
    .feedback-box p, .feedback-box div {
        margin-bottom: 0.5rem;
    }
    .feedback-box h3 {
        margin-top: 0;
        margin-bottom: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🔵 Atlas-Toppan Ticket Checker</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">🏢 System Support Team - 17-Step Workflow Integration</p>', unsafe_allow_html=True)

# Display Critical Rule
with st.container():
    col_rule1, col_rule2 = st.columns(2)
    with col_rule1:
        st.markdown("""
        <div class="validation-box">
        <span class="rule-badge validation-badge">🔵 VALIDATION</span><br>
        <strong>Steps 5,7,9</strong><br>
        • LEGACY_VALID<br>
        • ABIS_VALID<br>
        • WATCHLIST<br>
        <span style='color: #2196F3;'>System automatic → RAISE TICKET if stuck</span>
        </div>
        """, unsafe_allow_html=True)
    with col_rule2:
        st.markdown("""
        <div class="adjudication-box">
        <span class="rule-badge adjudication-badge">🟢 ADJUDICATION</span><br>
        <strong>Steps 6,8,10</strong><br>
        • LEGACY_ADJUD<br>
        • MANUAL_ADJUD<br>
        • WATCHLIST_ADJUD<br>
        <span style='color: #4CAF50;'>Officer manual → FOLLOW UP with ICS</span>
        </div>
        """, unsafe_allow_html=True)

# Create two columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    # Input form
    with st.form("ticket_form"):
        summary = st.text_input("📝 Ticket Summary", 
                               value=st.session_state.template_summary,
                               placeholder="Include AAPP number if available...")
        description = st.text_area("📝 Ticket Description", 
                                  value=st.session_state.template_description,
                                  height=200, 
                                  placeholder="Include: Current stage (1-17), Issue details, Expected action, Location if relevant...")
        
        # Additional options
        with st.expander("⚙️ Advanced Options & Stage Selection"):
            stage_options = list(WORKFLOW_MAPPING.values())
            
            current_stage = st.selectbox(
                "Current Stage",
                stage_options[:6]
            )
            
            current_stage2 = st.selectbox(
                "Continued",
                stage_options[6:12]
            )
            
            current_stage3 = st.selectbox(
                "Final Stages",
                stage_options[12:]
            )
            
            ticket_type = st.selectbox(
                "Issue Category",
                ["Type Change Request", "Biometric Issue", "Stuck Application", 
                 "Data Error", "Cancellation Request", "Payment Issue", "Status & Workflow Issues"]
            )
            priority = st.select_slider(
                "Priority",
                options=["Low", "Medium", "High", "Critical"]
            )
            location = st.text_input("Location/Branch (if relevant)", placeholder="e.g., KALITY, Semera")
        
        submitted = st.form_submit_button("🔍 Check Ticket", use_container_width=True)

with col2:
    # Quick stats and tips
    st.markdown("### 📊 Today's Stats")
    
    if 'tickets_checked' not in st.session_state:
        st.session_state.tickets_checked = 0
        st.session_state.tickets_raised = 0
        st.session_state.follow_ups = 0
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f'<div class="stats-card">📋<br/>Tickets Checked<br/><h2>{st.session_state.tickets_checked}</h2></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f'<div class="stats-card">✅<br/>Issues Found<br/><h2>{st.session_state.tickets_checked}</h2></div>', unsafe_allow_html=True)
    
    st.markdown("### 📋 17-Step Workflow")
    workflow_df = pd.DataFrame({
        "Step": range(1, 18),
        "Name": ["INITIATE", "PAYMENT", "VERIFICATION", "BIOMETRIC", "LEGACY_VALID", 
                "LEGACY_ADJUD", "ABIS_VALID", "MANUAL_ADJUD", "WATCHLIST", 
                "WATCHLIST_ADJUD", "AUTHORIZE", "ORDERED", "PERSO", "PRODUCED", 
                "RECEIVED", "ISSUED", "COMPLETED"],
        "Owner": ["customer", "customer/flayget", "officer", "officer", "VALIDATION", 
                 "ADJUDICATION", "VALIDATION", "ADJUDICATION", "VALIDATION",
                 "ADJUDICATION", "officer", "system", "PERSO", "OTHER", 
                 "OTHER", "OTHER", "OTHER"]
    })
    
    def color_type(val):
        if val == "VALIDATION":
            return 'background-color: #2196F3; color: white'
        elif val == "ADJUDICATION":
            return 'background-color: #4CAF50; color: white'
        return ''
    
    st.dataframe(workflow_df.style.applymap(color_type, subset=['Owner']), height=400)
    
    st.markdown("### 💡 Tips for Good Tickets")
    st.info(
        """
        • Single ARN only! (never batch multiple)
        • Include AAPP/ACPP number in summary
        • Specify current stage (1-17)
        • Describe the issue clearly
        • State expected action
        • Add location if relevant
        • Attach evidence when possible
        """
    )

# Process the ticket when submitted
if submitted:
    if not summary or not description:
        st.error("⚠️ Please fill in both summary and description!")
    else:
        with st.spinner("🤔 Analyzing against 17-step workflow and 50+ real tickets..."):
            try:
                arns = re.findall(r'(AAPP|ACPP|AEPP|BSPP|AAPO|MSPP)\d+[A-Z0-9]+', description)
                multiple_arns = len(arns) > 1
                
                selected_full = current_stage if 'current_stage' in locals() else "Not specified"
                
                prompt = f"""
You are an Atlas-Toppan System Support senior engineer who has analyzed 50+ real tickets.

GOOD TICKET EXAMPLES (use these as benchmarks):
{GOOD_TICKET_EXAMPLES}

BAD TICKET EXAMPLES (avoid these):
{BAD_TICKET_EXAMPLES}

COMPLETE 17-STEP WORKFLOW:
{WORKFLOW_MAPPING}

CRITICAL RULE:
- Steps 5,7,9 (LEGACY_VALID, ABIS_VALID, WATCHLIST) = VALIDATION → RAISE TICKET
- Steps 6,8,10 (LEGACY_ADJUD, MANUAL_ADJUD, WATCHLIST_ADJUD) = ADJUDICATION → FOLLOW UP

Ticket Details:
Category: {ticket_type}
Priority: {priority}
Location: {location}
Summary: {summary}
Description: {description}

ARNs found: {arns}
Multiple ARNs: {'YES - BAD PRACTICE' if multiple_arns else 'NO - GOOD'}

Analyze this ticket and provide feedback in this exact format:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 TICKET ANALYSIS RESULT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 CURRENT STAGE:
• Step: [Identify which step from 1-17]
• Name: [Stage name]
• Owner: [customer/officer/system/VALIDATION/ADJUDICATION]

⚠️ ARN CHECK: {'❌ MULTIPLE ARNs - Create separate tickets' if multiple_arns else '✅ Single ARN - Good'}

🔍 TICKET NEEDED: [YES if validation step or technical issue / NO if adjudication step / Depends]
• Reason: [One clear sentence]

🚀 ACTION REQUIRED:
• [RAISE TICKET to technical team or FOLLOW UP with ICS Officers]

✏️ IMPROVED TICKET (based on ESD-27018, ESD-26996, ESD-27026):
Summary: [Clear summary with ARN and issue type]

Description:
• ARN: {arns[0] if arns else '["Add ARN"]'}
• Current Stage: [Specific stage]
• Issue: [Specific problem]
• Action Requested: [Clear action]
• Reason: [Why this is needed]
• Evidence: [Attached files if any]

📊 QUALITY SCORE: [X/10]
• Compared to good examples: [Brief comparison]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a senior ACT System Support engineer. Use the real ticket examples as benchmarks."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1024
                )
                
                feedback = response.choices[0].message.content
                
                st.session_state.tickets_checked += 1
                if multiple_arns:
                    st.session_state.follow_ups += 1
                
                # Display feedback with reduced spacing
                st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
                st.markdown("### 🔍 AI Analysis Results")
                st.markdown(feedback)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Show ARN warning
                if multiple_arns:
                    st.error(f"❌ BAD PRACTICE: {len(arns)} ARNs found! Create ONE ticket per application. Found: {', '.join(arns[:3])}...")
                else:
                    st.success("✅ GOOD: Single ARN detected")
                
                # Extract and display quality score
                score_match = re.search(r'QUALITY SCORE:?\s*(\d+)/?10', feedback)
                if score_match:
                    score = int(score_match.group(1))
                    st.markdown(f"### 📊 Quality Score: {score}/10")
                    st.progress(score/10)
                    
                    if score >= 8:
                        st.success("🌟 Excellent ticket! Matches good examples like ESD-27018")
                    elif score >= 5:
                        st.warning("📝 Needs improvement - compare with ESD-26996")
                    else:
                        st.error("🔴 Poor ticket - don't batch multiple ARNs like the 'legacy stuck' example")
                
                # Add download button
                st.download_button(
                    label="📥 Download Feedback",
                    data=feedback,
                    file_name=f"ticket_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Please check your internet connection and API key.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        Atlas-Toppan System Support Team • 17-Step Workflow • 
        🔵 Validation = Ticket | 🟢 Adjudication = Follow up with ICS • One ARN = One Ticket
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar with templates only (no quick reference section)
with st.sidebar:
    st.markdown("## 📚 50+ Quality Templates")
    
    # Complete template library
    template_library = {
        "Photo Issues": {
            "Photo Too Large": {
                "summary": "URGENT - Application Rejected: Photo Too Large",
                "description": """AAPP4260C07777P

This application was rejected from PERSO because: "Applicant's photo is too large"

Please resize the photo according to passport specifications (35x45mm, 300 DPI) and reprocess.

Attachment: rejected_photo.jpeg""",
                "stage": "PERSO"
            },
            "Photo Too Small": {
                "summary": "Photo Resize Required - Below Minimum Size",
                "description": """ACPP52500B25A4P

Application rejected at PERSO due to: "Photo dimensions below minimum requirement"

Current photo: 30x40mm
Required: 35x45mm minimum

Please resize to meet ICAO standards and resubmit.

Attachment: current_photo.jpeg""",
                "stage": "PERSO"
            },
            "Photo Background": {
                "summary": "Photo Background Correction Needed",
                "description": """AAPP4260C222B6P

Application flagged at biometric validation: "Photo background must be plain white"

Current background shows pattern/shadow. Please replace with plain white background photo.

Requirements:
- Plain white background (RGB: 255,255,255)
- No shadows
- Even lighting

Attachment: current_photo.jpeg""",
                "stage": "BIOMETRIC"
            }
        },
        
        "Stuck in Workflow": {
            "Stuck at DOCUMENT_ORDERED": {
                "summary": "URGENT - Application Stuck at DOCUMENT_ORDERED (Step 12)",
                "description": """ACPP525004E251P

This application has been at DOCUMENT_ORDERED for 48+ hours. Normal processing time is 2-4 hours.

Current Status:
- Step: 12 (ORDERED - Backend)
- Time stuck: 48 hours
- ARN: ACPP525004E251P

Please investigate and force-proceed if backend issue.

Logs show: "Document generation queue timeout"

Location: ADDIS ABABA""",
                "stage": "ORDERED"
            },
            "Stuck at ABIS": {
                "summary": "ABIS Validation Stuck - System Timeout",
                "description": """ACPP5250056762P

Application stuck at ABIS_VALID (Step 7) for 6 hours.

Issue: ABIS system not responding to validation requests
Step: 7 - ABIS_VALID
Owner: VALIDATION

Please check ABIS service and restart if needed. This is affecting multiple applications in queue.

Screenshot attached: abis_timeout.png""",
                "stage": "ABIS_VALID"
            },
            "Stuck at Watchlist": {
                "summary": "Watchlist Validation Hung - System Check Required",
                "description": """ACPP5250063A30P

Application cannot proceed past WATCHLIST validation (Step 9).

Error in logs: "Watchlist service connection refused"

Please:
1. Check watchlist service status
2. Restart if necessary
3. Force-proceed this application once service is restored

Attachment: error_logs.txt""",
                "stage": "WATCHLIST"
            }
        },
        
        "Type Changes": {
            "Ordinary to Reissue (Lost)": {
                "summary": "URGENT - Type Change: Ordinary to Reissue (Lost)",
                "description": """ACPP52500B25A4P

Application was initiated as Ordinary Passport. Applicant reported passport lost and needs Reissue - Lost.

Current: Ordinary
Requested: Reissue (Lost)

Required changes:
1. Update application type to "Reissue - Lost"
2. Update fee calculation
3. Add lost report reference: LOST/2024/1234

Supporting documents attached:
- Lost report.pdf
- Applicant affidavit.pdf""",
                "stage": "INITIATE"
            },
            "Expired to Lost": {
                "summary": "URGENT - Status Change: EXPIRED TO LOST",
                "description": """ACPP52500B25A4P

This application was marked as EXPIRED but should be LOST.

Current status: EXPIRED
Correct status: LOST

Please make the change and sync to KALITY to ensure proper workflow.

Reason: Applicant reported passport lost before expiry date.

Attachment: police_report.pdf""",
                "stage": "INITIATE"
            },
            "Ordinary to Reissue (Expired)": {
                "summary": "Application Type Change - Ordinary to Reissue (Expired)",
                "description": """AAPP4260C222B6P

Application was initiated as Ordinary Passport. Please update to Reissue - Document Expired.

Current: Ordinary
Requested: Reissue - Document Expired

Reason: Applicant's passport expired on 2024-01-15

Supporting document: expired_passport_copy.pdf""",
                "stage": "INITIATE"
            }
        },
        
        "Biometric Issues": {
            "Merge Error": {
                "summary": "URGENT - Biometric Merge Error at Step 4",
                "description": """BSPP202403001

Biometric capture failed to merge with application.

Error: "Biometric template merge failed - applicant ID mismatch"
Step: 4 - BIOMETRIC
Location: SEMERA Branch

Applicant attempted biometric capture twice. System shows two separate records that need merging.

Please merge biometric records and restart workflow.

Attachments:
- error_screenshot.png
- biometric_logs.txt""",
                "stage": "BIOMETRIC"
            },
            "Missing Biometrics": {
                "summary": "Missing Biometrics - Application Incomplete",
                "description": """MSPP202403089

Application cannot proceed - no biometric data found.

Step: 4 - BIOMETRIC
Issue: "No fingerprints captured"

Applicant was at SEMERA branch but system shows zero biometric records.

Please verify if biometric device was working and recapture if possible.

Location: SEMERA""",
                "stage": "BIOMETRIC"
            }
        },
        
        "Cancellations": {
            "With Supervisor Approval": {
                "summary": "Application Cancellation Request - Supervisor Approved",
                "description": """AAPP4260C07777P

Request to cancel this application with supervisor approval.

ARN: AAPP4260C07777P
Reason: Applicant submitted duplicate application
Supervisor: Alemitu Bekele (ID: AB2024)
Approval ref: SUP/CANCEL/2024/089

Please cancel and process refund if payment was made.

Attached: supervisor_approval.pdf""",
                "stage": "Any"
            },
            "Duplicate Cancellation": {
                "summary": "URGENT - Cancel Duplicate Application",
                "description": """ACPP52500564F6P

Please cancel this application as it's a duplicate.

Original valid application: ACPP52500564F6P
Duplicate to cancel: ACPP52500564F7P

Applicant created two applications by mistake. Keep the first one, cancel the second.

Location: ADDIS ABABA""",
                "stage": "Any"
            }
        },
        
        "Data Correction": {
            "Name Spelling": {
                "summary": "Data Correction - Name Spelling Error",
                "description": """AAPP4260C222B6P

Please correct name spelling in the system.

Current: "Taddese Hailu"
Correct: "Tadesse Hailu"

Supporting document: passport_copy.pdf (shows correct spelling)

This needs correction before printing.""",
                "stage": "VERIFICATION"
            },
            "DOB Correction": {
                "summary": "Date of Birth Correction Required",
                "description": """ACPP5250063A30P

Date of birth entered incorrectly during application.

Current DOB: 1990-13-01 (invalid)
Correct DOB: 1990-01-13

Supporting evidence: birth_certificate.pdf attached

Please correct in system and recalculate age if needed for fees.""",
                "stage": "VERIFICATION"
            }
        },
        
        "Payment Issues": {
            "Fee Correction": {
                "summary": "Payment Fee Correction - Wrong Amount Charged",
                "description": """AAPP4260C222B6P

Incorrect fee charged for this application.

Charged: 2000 ETB (Ordinary)
Should be: 3000 ETB (Reissue - Lost)

Please adjust payment and generate new receipt.

Transaction ID: TXN20240315089
Date: 2024-03-15""",
                "stage": "PAYMENT"
            },
            "Duplicate Payment": {
                "summary": "Duplicate Payment - Refund Request",
                "description": """ACPP525004E251P

Applicant made two payments for same application.

Transaction 1: TXN20240315001 - 2000 ETB (successful)
Transaction 2: TXN20240315002 - 2000 ETB (duplicate)

Please cancel duplicate payment and process refund to original payment method.

Receipts attached: both_transactions.pdf""",
                "stage": "PAYMENT"
            }
        },
        
        "Status & Workflow Issues": {
            "Wrong Status Update": {
                "summary": "Status Update Error - Application Marked Complete Prematurely",
                "description": """ACPP5250047AE3P

Application incorrectly marked as COMPLETED (Step 17).

Actual status: Should be at PRODUCED (Step 13)
Card not yet printed/issued.

Please revert status to PRODUCED and restart workflow.

Location: ADDIS ABABA""",
                "stage": "COMPLETED"
            }
        }
    }
    
    # Category selection
    main_category = st.selectbox("Select Category", list(template_library.keys()))
    
    if main_category:
        sub_category = st.selectbox("Select Template", list(template_library[main_category].keys()))
        
        if sub_category:
            template = template_library[main_category][sub_category]
            
            with st.expander("📋 Preview Template", expanded=True):
                st.markdown(f"**Stage:** {template['stage']}")
                st.markdown(f"**Summary:** {template['summary']}")
                st.markdown("**Description:**")
                st.text(template['description'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Use This Template", use_container_width=True):
                    st.session_state.template_summary = template['summary']
                    st.session_state.template_description = template['description']
                    st.rerun()
            
            with col2:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.code(f"Summary: {template['summary']}\n\nDescription:\n{template['description']}")