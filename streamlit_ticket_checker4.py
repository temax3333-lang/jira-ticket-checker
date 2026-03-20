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
VALIDATION_STEPS = [5, 7, 9]  # LEGACY_VALID, ABIS_VALID, WATCHLIST
ADJUDICATION_STEPS = [6, 8, 10]  # LEGACY_ADJUD, MANUAL_ADJUD, WATCHLIST_ADJUD

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

# Custom CSS (EXACTLY as provided)
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
        padding: 2rem;
        border-radius: 1rem;
        border-left: 5px solid #FF4B4B;
        margin-top: 2rem;
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
    .good-section {
        color: #00FF00;
        font-weight: bold;
    }
    .fix-section {
        color: #FFA500;
        font-weight: bold;
    }
    .stats-card {
        background: linear-gradient(135deg, #262730, #1E1E1E);
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        border: 1px solid #FF4B4B;
    }
    .workflow-step {
        background-color: #0E1117;
        padding: 0.5rem;
        border-radius: 0.3rem;
        font-family: monospace;
        border: 1px solid #333;
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
        summary = st.text_input("📝 Ticket Summary", placeholder="Include AAPP number if available...")
        description = st.text_area("📝 Ticket Description", height=200, 
                                  placeholder="Include: Current stage (1-17), Issue details, Expected action, Location if relevant...")
        
        # Additional options
        with st.expander("⚙️ Advanced Options & Stage Selection"):
            # Updated with your exact workflow names
            stage_options = list(WORKFLOW_MAPPING.values())
            
            current_stage = st.selectbox(
                "Current Stage",
                stage_options[:6]  # First 6
            )
            
            current_stage2 = st.selectbox(
                "Continued",
                stage_options[6:12]  # Next 6
            )
            
            current_stage3 = st.selectbox(
                "Final Stages",
                stage_options[12:]  # Last 5
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
    
    # Initialize session state for stats if not exists
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
    
    # Color code the dataframe
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
                # Extract ARNs
                arns = re.findall(r'(AAPP|ACPP|AEPP|BSPP|AAPO|MSPP)\d+[A-Z0-9]+', description)
                multiple_arns = len(arns) > 1
                
                # Get stage info
                selected_full = current_stage if 'current_stage' in locals() else "Not specified"
                
                # Create the prompt with your real ticket examples
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
                
                # Call Groq API
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
                
                # Update stats
                st.session_state.tickets_checked += 1
                if multiple_arns:
                    st.session_state.follow_ups += 1
                
                # Display feedback in a nice box
                st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
                st.markdown("### 🔍 AI Analysis Results")
                st.markdown("---")
                st.markdown(feedback)
                
                # Show ARN warning prominently
                if multiple_arns:
                    st.error(f"❌ BAD PRACTICE: {len(arns)} ARNs found! Create ONE ticket per application. Found: {', '.join(arns[:3])}...")
                else:
                    st.success("✅ GOOD: Single ARN detected")
                
                # Extract and display quality score
                score_match = re.search(r'QUALITY SCORE:?\s*(\d+)/?10', feedback)
                if score_match:
                    score = int(score_match.group(1))
                    st.markdown("---")
                    st.markdown(f"### 📊 Quality Score: {score}/10")
                    st.progress(score/10)
                    
                    # Color code based on score
                    if score >= 8:
                        st.success("🌟 Excellent ticket! Matches good examples like ESD-27018")
                    elif score >= 5:
                        st.warning("📝 Needs improvement - compare with ESD-26996")
                    else:
                        st.error("🔴 Poor ticket - don't batch multiple ARNs like the 'legacy stuck' example")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Add download button for feedback
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

# Sidebar with additional info
 # Add this in your sidebar section (around line 400-450)
with st.sidebar:
    st.markdown("## 📚 50+ Quality Templates")
    
    template_categories = {
        "Photo Issues": ["Photo Too Large", "Photo Too Small", "Photo Background"],
        "Stuck in Workflow": ["Stuck at DOCUMENT_ORDERED", "Stuck at ABIS", "Stuck at Watchlist"],
        "Type Changes": ["Ordinary to Reissue (Lost)", "Expired to Lost", "Ordinary to Reissue (Expired)"],
        "Biometric Issues": ["Merge Error", "Missing Biometrics", "Age Error"],
        "Cancellations": ["With Supervisor Approval", "Duplicate Cancellation"],
        "Data Correction": ["Name Spelling", "DOB Correction", "ID Number"],
        "Payment Issues": ["Fee Correction", "Duplicate Payment", "Receipt Missing"]
    }
    
    selected_cat = st.selectbox("Choose category", list(template_categories.keys()))
    
    if selected_cat:
        templates = template_categories[selected_cat]
        selected_template = st.selectbox("Choose template", templates)
        
        if st.button("Show Template"):
            st.info(f"**Summary:** {selected_template}\n\n**Description:** [Full description from your templates]")

 with st.sidebar:
    st.markdown("## 📚 Quick Reference")
    
    with st.expander("🔵 VALIDATION Stages (RAISE TICKET)"):
        st.markdown("""
        - **Step :** LEGACY_VALID
        - **Step :** ABIS_VALID  
        - **Step :** WATCHLIST
        
        *If stuck → System issue → RAISE TICKET*
        """)
    
    with st.expander("🟢 ADJUDICATION Stages (FOLLOW UP)"):
        st.markdown("""
        - **Step :** LEGACY_ADJUD
        - **Step :** MANUAL_ADJUD
        - **Step :** WATCHLIST_ADJUD
        
        *If stuck → Officer issue → FOLLOW UP WITH ICS*
        """)
    
    with st.expander("📋 Good Examples to Follow"):
        st.markdown("""
        **ESD-27018:** EXPIRED TO LOST
        - Single ARN, clear before/after
        
        **ESD-26996:** Ordinary to Reissue
        - Single ARN, reason stated
        
        **ESD-27026:** Rejected from PERSO
        - Exact error message included
        """)
    
    with st.expander("📋 Bad Examples to Avoid"):
        st.markdown("""
        **"legacy stuck"**
        - 10 ARNs in one ticket
        - Generic description
        - No clear action
        """)
    
    st.markdown("---")
    st.markdown("### 🆘 Need Help?")
    st.markdown("Contact: System Support Team")
    st.markdown("Guide: Ticket Creation Guide v1.0")