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

DELIVERY_STATUSES = [
    "Not Sent",
    "Ready for Pickup",
    "Picked Up",
    "In Transit",
    "Arrived at Clinic",
    "Delivered",
    "Delayed",
    "Problem"
]

COLUMNS = [
    "Case ID", "Patient Code", "Clinic", "Denture Type",
    "Status", "Delivery Status", "Courier", "Tracking Number",
    "Current Location", "Receiver", "Date Sent",
    "Expected Delivery", "Notes", "AI Result",
    "Image File", "Created At"
]

# ---------- DATA ----------
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

# ---------- AI ----------
def ai_check_text(status, notes):
    notes_text = str(notes).lower()

    if status == "Problem":
        return "⚠️ Urgent review required."

    if "crack" in notes_text or "broken" in notes_text:
        return "⚠️ Possible defect detected."

    if status == "Quality Check":
        return "🔍 Ready for inspection."

    if status == "Completed":
        return "✅ Completed."

    return "ℹ️ Normal workflow."

def analyze_image(uploaded_image, case_id):
    if uploaded_image is None:
        return "No image uploaded.", ""

    image = Image.open(uploaded_image).convert("RGB")
    path = os.path.join(IMAGE_FOLDER, f"{case_id}.png")
    image.save(path)

    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    score = np.sum(edges > 0) / edges.size

    if score > 0.18:
        result = "🧠 Image AI: Complex structure, review carefully."
    elif score > 0.08:
        result = "🧠 Image AI: Moderate detail."
    else:
        result = "🧠 Image AI: Low detail, retake image."

    return result, path

# ---------- LOGIN ----------
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.title("IKASEL Login")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if password == "Earth2026":
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Wrong password")

    return False

# ---------- APP ----------
if check_password():

    st.title("🦷 IKASEL Denture Tracking + Delivery System")

    st.warning("Use patient codes only. No personal data.")

    df_cases = load_cases()

    # ---------- METRICS ----------
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cases", len(df_cases))
    col2.metric("In Transit", len(df_cases[df_cases["Delivery Status"] == "In Transit"]) if not df_cases.empty else 0)
    col3.metric("Delivered", len(df_cases[df_cases["Delivery Status"] == "Delivered"]) if not df_cases.empty else 0)

    # ---------- ADD CASE ----------
    st.subheader("➕ Add Case")

    uploaded_image = st.file_uploader("Upload Image", type=["jpg", "png"])

    with st.form("form"):
        patient_code = st.text_input("Patient Code")
        clinic = st.text_input("Clinic")
        denture_type = st.selectbox("Type", ["Full", "Partial"])
        status = st.selectbox("Workflow Status", STATUSES)
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Save")

        if submitted:
            case_id = f"IKJ-{len(df_cases)+1:04d}"

            ai_text = ai_check_text(status, notes)
            img_text, path = analyze_image(uploaded_image, case_id)

            new_case = {
                "Case ID": case_id,
                "Patient Code": patient_code,
                "Clinic": clinic,
                "Denture Type": denture_type,
                "Status": status,
                "Delivery Status": "Not Sent",
                "Courier": "",
                "Tracking Number": "",
                "Current Location": "",
                "Receiver": "",
                "Date Sent": "",
                "Expected Delivery": "",
                "Notes": notes,
                "AI Result": ai_text + " | " + img_text,
                "Image File": path,
                "Created At": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            save_case(new_case)
            st.success("Saved")
            st.rerun()

    # ---------- TABLE ----------
    st.subheader("📋 Cases")
    st.dataframe(df_cases)

    # ---------- DELIVERY MANAGEMENT ----------
    st.subheader("🚚 Delivery Tracking")

    df_all = load_cases()

    if not df_all.empty:
        for i, row in df_all.iterrows():
            with st.expander(f"{row['Case ID']} - {row['Patient Code']}"):

                st.write("### Delivery Info")

                delivery_status = st.selectbox(
                    "Delivery Status",
                    DELIVERY_STATUSES,
                    index=DELIVERY_STATUSES.index(row["Delivery Status"]) if row["Delivery Status"] in DELIVERY_STATUSES else 0,
                    key=f"ds_{i}"
                )

                courier = st.text_input("Courier", value=row["Courier"], key=f"c_{i}")
                tracking = st.text_input("Tracking Number", value=row["Tracking Number"], key=f"t_{i}")
                location = st.text_input("Current Location", value=row["Current Location"], key=f"l_{i}")
                receiver = st.text_input("Receiver", value=row["Receiver"], key=f"r_{i}")

                date_sent = st.date_input("Date Sent", key=f"d_{i}")
                expected = st.date_input("Expected Delivery", key=f"e_{i}")

                if st.button("Update Delivery", key=f"u_{i}"):
                    df_all.at[i, "Delivery Status"] = delivery_status
                    df_all.at[i, "Courier"] = courier
                    df_all.at[i, "Tracking Number"] = tracking
                    df_all.at[i, "Current Location"] = location
                    df_all.at[i, "Receiver"] = receiver
                    df_all.at[i, "Date Sent"] = str(date_sent)
                    df_all.at[i, "Expected Delivery"] = str(expected)

                    save_all_cases(df_all)
                    st.success("Updated")
                    st.rerun()

    # ---------- CHART ----------
    st.subheader("📊 Delivery Status Chart")

    if not df_all.empty:
        st.bar_chart(df_all["Delivery Status"].value_counts())

    # ---------- EXPORT ----------
    csv = df_all.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "delivery_report.csv")
