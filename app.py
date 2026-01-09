import streamlit as st
import pandas as pd
from guard import run_audit, exterior_scan, draw_manual_overlay
import os

# 1. SET PAGE CONFIG
st.set_page_config(page_title="Revenue Guard AI", page_icon="🛡️", layout="wide")

# 2. DEFINE RO NUMBER & INVENTORY
query_params = st.query_params
ro_num = query_params.get("ro", "RO-500")

INVENTORY = {
    "P101": {"name": "Oil Filter", "price": 85.00},
    "P102": {"name": "Brake Pads", "price": 120.00},
    "P103": {"name": "Plastic Clip", "price": 5.00},
    "P104": {"name": "Headlight Assembly", "price": 600.00},
    "P105": {"name": "Front Bumper", "price": 1200.00}
}

# 3. RECONCILIATION LOGIC
def check_billing_discrepancy(visual_finding, ro_id):
    try:
        invoice_df = pd.read_csv('final_invoice.csv')
        current_invoice = invoice_df[invoice_df['ro_id'].astype(str) == str(ro_id)]
        detected_part = visual_finding.split('|')[0].split('PART:')[-1].strip().lower()
        billed_items = " ".join(current_invoice['item_name'].astype(str).tolist()).lower()
        
        if detected_part not in billed_items:
            return f"🚨 Technician has not mentioned the {detected_part.upper()} in the final invoice. Please check again."
        return f"✅ Verified: {detected_part.upper()} is documented."
    except Exception as e:
        return f"Reconciliation Error: {e}"

# 4. INITIAL TECHNICIAN PORTAL
if 'billing_complete' not in st.session_state:
    st.session_state.billing_complete = False
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

if not st.session_state.billing_complete:
    st.header(f"🔧 Technician Portal: Billing & Notes (RO: {ro_num})")
    with st.form("billing_form"):
        selected_part_names = st.multiselect("Select Parts Used from Inventory", options=[v["name"] for v in INVENTORY.values()])
        input_note = st.text_area("Describe the work performed...", placeholder="e.g. Changed the oil and replaced bumper...")
        submit_btn = st.form_submit_button("Finish & Open Audit Dashboard")
        
        if submit_btn:
            invoice_data = []
            for name in selected_part_names:
                item_id = [k for k, v in INVENTORY.items() if v["name"] == name][0]
                price = INVENTORY[item_id]["price"]
                invoice_data.append({"ro_id": ro_num, "item_id": item_id, "item_name": name, "billed_price": price})
            pd.DataFrame(invoice_data).to_csv('final_invoice.csv', index=False)
            pd.DataFrame([{"ro_id": ro_num, "note_text": input_note}]).to_csv('mechanic_notes.csv', index=False)
            st.session_state.billing_complete = True
            st.rerun()
    st.stop()

# --- 5. AUDIT DASHBOARD ---
if 'errors' not in st.session_state: st.session_state.errors = None
if 'ai_diag' not in st.session_state: st.session_state.ai_diag = None
if 'visual_findings' not in st.session_state: st.session_state.visual_findings = None
if 'highlighted_img' not in st.session_state: st.session_state.highlighted_img = None

st.title("🛡️ AI Revenue Guard")
st.markdown(f"### Auditing Repair Order: **{ro_num}**")

st.sidebar.header("Evidence Upload")
before_img = st.sidebar.file_uploader("Before Photo", type=['jpg', 'png', 'jpeg'])
after_img = st.sidebar.file_uploader("After Photo", type=['jpg', 'png', 'jpeg'])
uploaded_audio = st.sidebar.file_uploader("Engine Sound", type=["mp3", "wav"])

col_pre1, col_pre2 = st.columns(2)
with col_pre1:
    if before_img: st.image(before_img, caption="Before", use_container_width=True)
with col_pre2:
    if after_img: st.image(after_img, caption="After", use_container_width=True)

st.divider()

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
            if box: st.session_state.highlighted_img = draw_manual_overlay(af_path, box)
with btn2:
    if st.button("🔊 Engine Audio (Step 3)", use_container_width=True):
        if uploaded_audio:
            a_path = "temp_audio.mp3"
            with open(a_path, "wb") as f: f.write(uploaded_audio.getbuffer())
            _, diag = run_audit(ro_num, a_path)
            st.session_state.ai_diag = diag

st.divider()
left_report, right_details = st.columns([1, 1])

with left_report:
    st.subheader("📋 Final Audit & Revenue Report")
    if st.session_state.errors:
        st.write("**Digital Audit Results:**")
        for e in st.session_state.errors: st.error(e)
    if st.session_state.visual_findings:
        st.write("**Visual Audit Results:**")
        verdict = check_billing_discrepancy(st.session_state.visual_findings, ro_num)
        if "Technician" in verdict: st.error(verdict)
        else: st.success(verdict)

with right_details:
    with st.expander("🔍 Visual Evidence Detail", expanded=True):
        if st.session_state.highlighted_img:
            st.image(st.session_state.highlighted_img)
            st.info(st.session_state.visual_findings)
    with st.expander("🔊 Acoustic Diagnosis Detail", expanded=True):
        if st.session_state.ai_diag:
            raw_diag = st.session_state.ai_diag
            if "|" in raw_diag:
                diag_text = raw_diag.split("|")[0].replace("DIAGNOSIS:", "").strip()
                parts_text = raw_diag.split("|")[1].replace("PARTS:", "").strip()
                st.warning(f"**AI Sound Diagnosis:** {diag_text}")
                st.error(f"🛠️ **Responsible Parts:** {parts_text}")
            else: st.info(raw_diag)

# --- 6. FINAL SUBMISSION & BILLING ---
st.divider()
f1, f2 = st.columns(2)
with f1:
    if st.button("📤 Submit to Service Manager", type="primary", use_container_width=True):
        st.session_state.submitted = True
        st.balloons()
with f2:
    if st.button("🗑️ Reset Application", use_container_width=True):
        st.session_state.clear()
        st.rerun()

if st.session_state.submitted:
    st.divider()
    st.subheader("🧾 Final Customer Invoice")
    with st.container(border=True):
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.markdown(f"**Shop:** Revenue Guard Garage")
            st.markdown(f"**RO ID:** {ro_num}")
        with b_col2:
            st.markdown(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"**Status:** PAID & VERIFIED")
        
        st.divider()
        if os.path.exists('final_invoice.csv'):
            invoice_df = pd.read_csv('final_invoice.csv')
            st.table(invoice_df[['item_id', 'item_name', 'billed_price']].rename(columns={'item_id':'ID', 'item_name':'Part', 'billed_price':'Price ($)'}))
            total = invoice_df['billed_price'].sum()
            st.markdown(f"### Total Amount: ${total:.2f}")
            
            # Final Send Button with Balloon effect
            if st.button("📧 Send Invoice to Customer", use_container_width=True):
                st.balloons()
                st.snow() # Bonus "car-coolant" effect
                st.success(f"Invoice for {ro_num} sent to customer's email!")