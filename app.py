import os
import cv2
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from datetime import datetime

DATA_FILE = "denture_cases.csv"
IMAGE_FOLDER = "uploaded_images"

os.makedirs(IMAGE_FOLDER, exist_ok=True)

st.set_page_config(
    page_title="IKASEL Denture Tracker",
    page_icon="🦷",
    layout="wide"
)

STATUSES = [
    "Received", "Scanned", "Designing", "Manufacturing",
    "Quality Check", "Packed", "Sent to Hospital",
    "Completed", "Problem"
]

COLUMNS = [
    "Case ID", "Patient Code", "Clinic", "Denture Type",
    "Status", "Notes", "AI Result", "Image File", "Created At"
]

def load_cases():
    try:
        df = pd.read_csv(DATA_FILE)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUMNS)

def save_all_cases(df):
    df.to_csv(DATA_FILE, index=False)

def save_case(case):
    df = load_cases()
    df = pd.concat([df, pd.DataFrame([case])], ignore_index=True)
    save_all_cases(df)

def ai_check_text(status, notes):
    notes_text = str(notes).lower()

    if status == "Problem":
        return "⚠️ Urgent review required."

    if "crack" in notes_text or "broken" in notes_text or "mismatch" in notes_text:
        return "⚠️ Possible defect detected from notes. Review before delivery."

    if status == "Quality Check":
        return "🔍 Ready for final inspection."

    if status == "Completed":
        return "✅ Completed successfully."

    return "ℹ️ Normal workflow."

def analyze_image(uploaded_image, case_id):
    if uploaded_image is None:
        return "No image uploaded.", ""

    image = Image.open(uploaded_image).convert("RGB")
    image_path = os.path.join(IMAGE_FOLDER, f"{case_id}.png")
    image.save(image_path)

    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    edge_score = np.sum(edges > 0) / edges.size

    if edge_score > 0.18:
        result = "🧠 Image AI: High edge complexity detected. Review structure carefully."
    elif edge_score > 0.08:
        result = "🧠 Image AI: Moderate structure detected. Suitable for review."
    else:
        result = "🧠 Image AI: Low structure detail detected. Image may need retake."

    return result, image_path

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.markdown("<h1 style='text-align:center;'>🦷 IKASEL Secure Login</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Denture Tracking + AI Support System</p>", unsafe_allow_html=True)

    password = st.text_input("Access Password", type="password")

    if st.button("Login", use_container_width=True):
        if password == "Earth2026":
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Wrong password")

    return False

if check_password():
    st.sidebar.title("IKASEL System")
    st.sidebar.success("Authenticated")
    st.sidebar.info("Prototype: Tracking + Image AI + Reports")

    st.title("🦷 IKASEL Denture Tracking Dashboard")
    st.caption("Secure denture workflow tracking system with basic AI image support.")

    st.warning(
        "Use patient codes only. Do not enter full names, phone numbers, addresses, or detailed medical history."
    )

    df_cases = load_cases()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", len(df_cases))
    col2.metric("In Progress", len(df_cases[~df_cases["Status"].isin(["Completed", "Problem"])]) if not df_cases.empty else 0)
    col3.metric("Completed", len(df_cases[df_cases["Status"] == "Completed"]) if not df_cases.empty else 0)
    col4.metric("Problems", len(df_cases[df_cases["Status"] == "Problem"]) if not df_cases.empty else 0)

    st.divider()

    left, right = st.columns([1, 1.4])

    with left:
        st.subheader("➕ Add New Denture Case")

        uploaded_image = st.file_uploader(
            "Upload Denture Image",
            type=["jpg", "jpeg", "png"]
        )

        with st.form("case_form"):
            patient_code = st.text_input("Patient Code", placeholder="P-0001")
            clinic = st.text_input("Clinic / Hospital", placeholder="Clinic name")
            denture_type = st.selectbox(
                "Denture Type",
                ["Full Denture", "Partial Denture", "Upper Denture", "Lower Denture", "Other"]
            )
            status = st.selectbox("Workflow Status", STATUSES)
            notes = st.text_area("Notes", placeholder="Do not enter full patient identity")

            submitted = st.form_submit_button("Save Case", use_container_width=True)

            if submitted:
                if not patient_code or not clinic:
                    st.error("Please enter Patient Code and Clinic Name.")
                else:
                    case_id = f"IKJ-{len(df_cases) + 1:04d}"

                    text_ai = ai_check_text(status, notes)
                    image_ai, image_path = analyze_image(uploaded_image, case_id)

                    final_ai = text_ai + " | " + image_ai

                    new_case = {
                        "Case ID": case_id,
                        "Patient Code": patient_code,
                        "Clinic": clinic,
                        "Denture Type": denture_type,
                        "Status": status,
                        "Notes": notes,
                        "AI Result": final_ai,
                        "Image File": image_path,
                        "Created At": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }

                    save_case(new_case)
                    st.success(f"{case_id} saved successfully")
                    st.rerun()

    with right:
        st.subheader("🔍 Search & Filter")

        search_term = st.text_input("Search by Patient Code or Clinic")
        status_filter = st.selectbox("Filter by Status", ["All"] + STATUSES)

        filtered_df = df_cases.copy()

        if search_term and not filtered_df.empty:
            filtered_df = filtered_df[
                filtered_df["Patient Code"].astype(str).str.contains(search_term, case=False, na=False) |
                filtered_df["Clinic"].astype(str).str.contains(search_term, case=False, na=False)
            ]

        if status_filter != "All" and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df["Status"] == status_filter]

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        if not filtered_df.empty:
            st.subheader("🧠 Latest AI Insight")
            st.success(filtered_df.iloc[-1]["AI Result"])

    st.divider()

    st.subheader("🛠 Manage Cases")

    df_all = load_cases()

    if not df_all.empty:
        for i, row in df_all.iterrows():
            with st.expander(f"{row['Case ID']} - {row['Patient Code']}"):
                col_a, col_b = st.columns([1, 1])

                with col_a:
                    st.write(f"**Clinic:** {row['Clinic']}")
                    st.write(f"**Denture Type:** {row['Denture Type']}")
                    st.write(f"**Current Status:** {row['Status']}")
                    st.write(f"**Notes:** {row['Notes']}")
                    st.write(f"**AI Result:** {row['AI Result']}")

                    new_status = st.selectbox(
                        "Update Status",
                        STATUSES,
                        index=STATUSES.index(row["Status"]) if row["Status"] in STATUSES else 0,
                        key=f"status_{i}"
                    )

                    if st.button("Save Status", key=f"save_{i}"):
                        df_all.at[i, "Status"] = new_status
                        df_all.at[i, "AI Result"] = ai_check_text(new_status, row["Notes"])
                        save_all_cases(df_all)
                        st.success("Status updated")
                        st.rerun()

                    if st.button("Delete Case", key=f"delete_{i}"):
                        df_all = df_all.drop(i)
                        save_all_cases(df_all)
                        st.warning("Case deleted")
                        st.rerun()

                with col_b:
                    image_file = str(row.get("Image File", ""))

                    if image_file and image_file != "nan" and os.path.exists(image_file):
                        st.image(image_file, caption=f"Image for {row['Case ID']}", use_container_width=True)
                    else:
                        st.info("No image available for this case.")
    else:
        st.info("No cases available yet.")

    st.divider()

    chart_col, export_col = st.columns([1.2, 1])

    with chart_col:
        st.subheader("📈 Status Summary")

        df_all = load_cases()

        if not df_all.empty:
            st.bar_chart(df_all["Status"].value_counts())
        else:
            st.info("No case data yet.")

    with export_col:
        st.subheader("📤 Export Data")

        csv = df_all.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "Download CSV Report",
            csv,
            "denture_cases_report.csv",
            "text/csv",
            use_container_width=True
        )

        st.subheader("🧭 Workflow")
        st.info("Received → Scanned → Designing → Manufacturing → Quality Check → Packed → Sent to Hospital → Completed")

    st.divider()

    st.subheader("📌 Patent / Invention Note")
    st.info(
        "This prototype demonstrates a workflow for denture case tracking, image-based review support, "
        "status monitoring, audit-style records, and exportable reports. The advanced patent idea may focus "
        "on the unique verification method, image-analysis logic, workflow automation, and secure traceability."
    )