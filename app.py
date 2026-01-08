import streamlit as st
import pandas as pd
from guard import run_audit, exterior_scan, draw_manual_overlay
import os

st.set_page_config(page_title="Revenue Guard AI", page_icon="🛡️", layout="wide")

# --- LOGIC: RECONCILIATION ENGINE ---
def check_billing_discrepancy(visual_finding, ro_id):
    try:
        invoice_df = pd.read_csv('final_invoice.csv')
        current_invoice = invoice_df[invoice_df['ro_id'].astype(str) == str(ro_id)]
        detected_part = visual_finding.split('|')[0].split('PART:')[-1].strip().lower()
        billed_items = " ".join(current_invoice['item_name'].astype(str).tolist()).lower()
        
        if detected_part not in billed_items:
            return f"🚨 Technician has not mentioned the {detected_part.upper()} in the final invoice. Please check again with the technician."
        return f"✅ Verified: {detected_part.upper()} is documented in the billing."
    except Exception as e:
        return f"Reconciliation Error: {e}"

# --- SESSION STATE ---
if 'errors' not in st.session_state: st.session_state.errors = None
if 'ai_diag' not in st.session_state: st.session_state.ai_diag = None
if 'visual_findings' not in st.session_state: st.session_state.visual_findings = None
if 'highlighted_img' not in st.session_state: st.session_state.highlighted_img = None

st.title("🛡️ AI Revenue Guard")
st.markdown("### Multi-Modal Shop Audit Dashboard")

# --- SIDEBAR & PREVIEWS ---
st.sidebar.header("Upload Center")
ro_num = st.sidebar.text_input("Repair Order Number", "RO-500")
before_img = st.sidebar.file_uploader("Before Photo", type=['jpg', 'png', 'jpeg'])
after_img = st.sidebar.file_uploader("After Photo", type=['jpg', 'png', 'jpeg'])
uploaded_audio = st.sidebar.file_uploader("Engine Sound", type=["mp3", "wav"])

col_pre1, col_pre2 = st.columns(2)
with col_pre1:
    if before_img: st.image(before_img, caption="Before", use_container_width=True)
with col_pre2:
    if after_img: st.image(after_img, caption="After", use_container_width=True)

st.divider()

# --- STEP 1: ACTION BUTTONS ---
btn1, btn2, btn3 = st.columns(3)

with btn1:
    if st.button("📄 Scan Invoice (Step 1)", use_container_width=True):
        errors, _ = run_audit(ro_num, audio_path=None)
        st.session_state.errors = errors

with btn3:
    if st.button("📸 Visual Audit (Step 2)", use_container_width=True):
        if before_img and after_img:
            b_path, af_path = "temp_before.jpg", "temp_after.jpg"
            with open(af_path, "wb") as f: f.write(after_img.getbuffer())
            findings, box = exterior_scan(b_path, af_path, after_img.name)
            st.session_state.visual_findings = findings
            if box:
                st.session_state.highlighted_img = draw_manual_overlay(af_path, box)

with btn2:
    if st.button("🔊 Engine Audio (Step 3)", use_container_width=True):
        if uploaded_audio:
            a_path = "temp_audio.mp3"
            with open(a_path, "wb") as f: f.write(uploaded_audio.getbuffer())
            _, diag = run_audit(ro_num, a_path)
            st.session_state.ai_diag = diag

# --- STEP 2: ORGANIZED UI COLUMNS ---
st.divider()
left_report, right_details = st.columns([1, 1])

# LEFT COLUMN: THE FINAL AUDIT BRAIN
with left_report:
    st.subheader("📋 Final Audit & Revenue Report")
    
    # Show Digital Leak (from Scan Invoice)
    if st.session_state.errors:
        st.write("**Digital Audit Results:**")
        for e in st.session_state.errors:
            st.error(e)
            
    # Show Visual Leak (Reconciliation)
    if st.session_state.visual_findings:
        st.write("**Visual Audit Results:**")
        verdict = check_billing_discrepancy(st.session_state.visual_findings, ro_num)
        if "Technician has not mentioned" in verdict:
            st.error(verdict)
        else:
            st.success(verdict)
            
    if not st.session_state.errors and not st.session_state.visual_findings:
        st.info("Awaiting Invoice or Visual Scan...")

# RIGHT COLUMN: VISUAL & ACOUSTIC DETAILS
with right_details:
    # A. Visual Detail Bucket
    with st.expander("🔍 Visual Evidence Detail", expanded=True):
        if st.session_state.highlighted_img:
            st.image(st.session_state.highlighted_img, caption="AI Detection Highlight")
            st.info(f"AI Detected: {st.session_state.visual_findings}")
        else:
            st.write("No visual analysis performed yet.")

    # B. Acoustic Diagnosis Bucket
    # Inside the Acoustic Diagnosis Bucket in app.py:

with right_details:
    # ... (Keep Visual Evidence Detail above) ...

    # B. Acoustic Diagnosis Bucket
    with st.expander("🔊 Acoustic Diagnosis Detail", expanded=True):
        if st.session_state.ai_diag:
            try:
                # Split the AI response into Diagnosis and Parts
                raw_diag = st.session_state.ai_diag
                if "|" in raw_diag:
                    diag_text = raw_diag.split("|")[0].replace("DIAGNOSIS:", "").strip()
                    parts_text = raw_diag.split("|")[1].replace("PARTS:", "").strip()
                else:
                    diag_text = raw_diag
                    parts_text = "Analysis pending more data..."

                st.warning(f"**AI Sound Diagnosis:** {diag_text}")
                
                # THIS IS THE DYNAMIC PART FROM THE AI
                st.error(f"🛠️ **Responsible Parts:** {parts_text}")
                
            except Exception:
                st.info(st.session_state.ai_diag)
        else:
            st.write("No audio analysis performed yet.")

# --- STEP 3: FINAL ACTIONS ---
st.divider()
final1, final2 = st.columns(2)
with final1:
    if st.button("📤 Submit to Service Manager", type="primary", use_container_width=True):
        st.balloons()
        st.success("Report Sent.")
with final2:
    if st.button("🗑️ Reset", use_container_width=True):
        st.session_state.clear()
        st.rerun()