import streamlit as st
from groq import Groq
import pandas as pd
from datetime import datetime
import os  # ADD THIS LINE

# Page configuration
st.set_page_config(
    page_title="Jira Ticket Checker",
    page_icon="🤖",
    layout="wide"
)

# Initialize Groq client
@st.cache_resource
def get_client():
    # FIXED: API key comes from environment variable, not hardcoded
    return Groq(api_key=os.environ["GROQ_API_KEY"])

client = get_client()

# Rest of your code remains exactly the same...
# (Keep everything else from your file after this line)

# ============================================
# WORKFLOW MAPPING (from your table)
# ============================================
WORKFLOW_DATA = {
    1: {"name": "INITIATE", "owner": "customer", "type": "OTHER"},
    2: {"name": "PAYMENT", "owner": "customer/flayget", "type": "OTHER"},
    3: {"name": "VERIFICATION", "owner": "officer", "type": "OTHER"},
    4: {"name": "BIOMETRIC", "owner": "officer", "type": "OTHER"},
    5: {"name": "LEGACY_VALID", "owner": "VALIDATION", "type": "VALIDATION"},
    6: {"name": "LEGACY_ADJUD", "owner": "ADJUDICATION", "type": "ADJUDICATION"},
    7: {"name": "ABIS_VALID", "owner": "VALIDATION", "type": "VALIDATION"},
    8: {"name": "MANUAL_ADJUD", "owner": "ADJUDICATION", "type": "ADJUDICATION"},
    9: {"name": "WATCHLIST", "owner": "VALIDATION", "type": "VALIDATION"},
    10: {"name": "WATCHLIST_ADJUD", "owner": "ADJUDICATION", "type": "ADJUDICATION"},
    11: {"name": "AUTHORIZE", "owner": "officer", "type": "OTHER"},
    12: {"name": "ORDERED", "owner": "system", "type": "OTHER"},
    13: {"name": "PERSO", "owner": "PERSO", "type": "OTHER"},
    14: {"name": "PRODUCED", "owner": "OTHER", "type": "OTHER"},
    15: {"name": "RECEIVED", "owner": "OTHER", "type": "OTHER"},
    16: {"name": "ISSUED", "owner": "OTHER", "type": "OTHER"},
    17: {"name": "COMPLETED", "owner": "OTHER", "type": "OTHER"}
}

# Rule for tickets
VALIDATION_STEPS = [5, 7, 9]  # System validation → RAISE TICKET
ADJUDICATION_STEPS = [6, 8, 10]  # Officer adjudication → FOLLOW UP

# Good ticket patterns from your data
GOOD_PATTERNS = """
✅ GOOD TICKET CHARACTERISTICS:
• Single ARN per ticket
• Format: AAPP, ACPP, AEPP, BSPP, AAPO, MSPP
• Current status mentioned
• Specific problem described
• Clear action requested
• Reason provided
• Evidence attached
"""

# Bad ticket patterns
BAD_PATTERNS = """
❌ BAD TICKET CHARACTERISTICS:
• Multiple ARNs in one ticket
• Generic summary like "legacy stuck"
• No specific problem
• No clear action
• Missing evidence
"""

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #FF4B4B; text-align: center; }
    .sub-header { font-size: 1.2rem; color: #FFFFFF; background: #0E1117; padding: 1rem; border-radius: 0.5rem; border-left: 5px solid #FF4B4B; }
    .feedback-box { background-color: #1E1E1E; padding: 2rem; border-radius: 1rem; border-left: 5px solid #FF4B4B; margin-top: 2rem; }
    .validation-box { background-color: #1E3A5F; padding: 1rem; border-radius: 0.5rem; border-left: 5px solid #2196F3; }
    .adjudication-box { background-color: #1E4A3F; padding: 1rem; border-radius: 0.5rem; border-left: 5px solid #4CAF50; }
    .stats-card { background: #262730; padding: 1rem; border-radius: 0.5rem; text-align: center; }
    .good-badge { background-color: #4CAF50; color: white; padding: 0.2rem 0.5rem; border-radius: 0.3rem; }
    .bad-badge { background-color: #F44336; color: white; padding: 0.2rem 0.5rem; border-radius: 0.3rem; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🔵 ACT Atlas-Topan Ticket Checker</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Based on 17-Step Workflow • One ARN = One Ticket</p>', unsafe_allow_html=True)

# Rule boxes
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="validation-box">
    <strong>🔵 VALIDATION STEPS: {VALIDATION_STEPS}</strong><br>
    LEGACY_VALID (5) • ABIS_VALID (7) • WATCHLIST (9)<br>
    <span style='color: #90CAF9;'>System automatic → RAISE TICKET if stuck</span>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="adjudication-box">
    <strong>🟢 ADJUDICATION STEPS: {ADJUDICATION_STEPS}</strong><br>
    LEGACY_ADJUD (6) • MANUAL_ADJUD (8) • WATCHLIST_ADJUD (10)<br>
    <span style='color: #A5D6A7;'>Officer manual → FOLLOW UP with ICS</span>
    </div>
    """, unsafe_allow_html=True)

# Main layout
col_input, col_info = st.columns([2, 1])

with col_input:
    with st.form("ticket_form"):
        summary = st.text_input("📝 Summary", placeholder="AAPP1234567890: Type change to Reissue (Lost)")
        description = st.text_area("📝 Description", height=200, 
                                  placeholder="ARN: AAPP...\nCurrent Status: VERIFICATION\nIssue: ...\nAction Requested: ...\nReason: ...")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            step = st.selectbox("Current Step", list(WORKFLOW_DATA.keys()), format_func=lambda x: f"{x}. {WORKFLOW_DATA[x]['name']}")
        with col_s2:
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
        
        location = st.text_input("Location", placeholder="KALITY, Semera, etc.")
        submitted = st.form_submit_button("🔍 Check Ticket", use_container_width=True)

with col_info:
    st.markdown("### 📊 Today")
    if 'count' not in st.session_state:
        st.session_state.count = 0
        st.session_state.good = 0
    
    st.markdown(f'<div class="stats-card">📋 Checked: {st.session_state.count}</div>', unsafe_allow_html=True)
    
    st.markdown("### ✅ Checklist")
    st.checkbox("Single ARN only")
    st.checkbox("Current status")
    st.checkbox("Clear action")
    st.checkbox("Reason given")
    
    # Workflow table
    st.markdown("### 📋 17-Step Workflow")
    df = pd.DataFrame([
        {"Step": k, "Name": v["name"], "Type": v["type"]} 
        for k, v in WORKFLOW_DATA.items()
    ])
    st.dataframe(df, height=300, use_container_width=True)

# Process ticket
if submitted:
    if not summary or not description:
        st.error("⚠️ Fill in both fields")
    else:
        st.session_state.count += 1
        
        with st.spinner("Analyzing..."):
            try:
                # Check for multiple ARNs
                arns = re.findall(r'(AAPP|ACPP|AEPP|BSPP|AAPO|MSPP)\d+[A-Z0-9]+', description)
                multiple_arns = len(arns) > 1
                
                # Determine step type
                step_type = WORKFLOW_DATA[step]["type"]
                action = "RAISE TICKET" if step in VALIDATION_STEPS else "FOLLOW UP WITH ICS" if step in ADJUDICATION_STEPS else "Check manually"
                
                prompt = f"""
You are an ACT ticket expert. Compare this ticket to real examples.

GOOD: {GOOD_PATTERNS}
BAD: {BAD_PATTERNS}

Ticket:
Summary: {summary}
Description: {description}
Step: {step} - {WORKFLOW_DATA[step]['name']}
Priority: {priority}
Location: {location}

ARNs found: {arns}
Multiple ARNs: {multiple_arns}

Give analysis in this exact format:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RESULT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP: {step} - {WORKFLOW_DATA[step]['name']}
TYPE: {step_type}
ACTION: {action}

QUALITY: [X/10]

GOOD:
- [list good points]

BAD:
- [list bad points]

FIXED SUMMARY:
[improved summary]

FIXED DESCRIPTION:
• ARN: [single ARN]
• Status: [current]
• Issue: [specific]
• Action: [clear]
• Reason: [why]
• Location: [where]
"""
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an ACT support engineer. Be concise."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    timeout=30
                )
                
                feedback = response.choices[0].message.content
                
                # Show result
                st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
                st.markdown(feedback)
                
                # Show ARN warning
                if multiple_arns:
                    st.error(f"❌ BAD: Multiple ARNs detected! Create separate tickets. Found: {', '.join(arns[:3])}...")
                else:
                    st.success("✅ GOOD: Single ARN detected")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Download
                st.download_button("📥 Download", feedback, file_name=f"ticket_{datetime.now().strftime('%H%M%S')}.txt")
                
            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>One ARN = One Ticket • Be Specific • Attach Evidence</div>", unsafe_allow_html=True)