
import streamlit as st
import fitz  # PyMuPDF
import docx2txt
import pandas as pd
import re
from io import BytesIO
from datetime import datetime

INTERVIEWERS = ["Nimal Perera", "Ishara Fernando", "Tharindu Jayasinghe", "Kasun Silva"]

def extract_text(file):
    text = ""
    if file.name.lower().endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc:
            text += page.get_text()
    elif file.name.lower().endswith((".docx", ".doc")):
        text = docx2txt.process(file)
    return text

def extract_field(text, pattern):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def calculate_age(dob_str):
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except:
        return "N/A"

def main():
    st.title("✈️ CV Shortlister Pro – Airport Assistant Hiring")

    st.sidebar.header("Set Shortlisting Criteria")
    min_ol = st.sidebar.selectbox("Min O/L English", ["A", "B", "C", "D"], index=2)
    min_al = st.sidebar.selectbox("Min A/L General English", ["A", "B", "C", "D"], index=2)
    require_exp = st.sidebar.checkbox("Require Customer Service Experience")
    min_age = st.sidebar.slider("Minimum Age", 18, 60, 18)
    max_age = st.sidebar.slider("Maximum Age", 18, 60, 40)

    uploaded = st.file_uploader("Upload CVs (PDF or DOCX)", accept_multiple_files=True)
    interview_log = []

    if uploaded:
        results = []
        cv_files = {}
        for f in uploaded:
            text = extract_text(f)
            name = f.name.rsplit(".", 1)[0]
            cv_files[name] = f

            ol_eng = extract_field(text, r"O/L.*?English.*?([A-E])")
            al_eng = extract_field(text, r"General English.*?([A-E])")
            eng_lit = extract_field(text, r"English Literature.*?([A-E])")
            university = extract_field(text, r"(University.*?)\n")
            town = extract_field(text, r"Address.*?[:,\n](.*?)\n")
            gender = "Female" if "Ms." in text or "Miss" in text else ("Male" if "Mr." in text else "Not Stated")
            dob_match = re.search(r"Date of Birth.*?(\d{4}-\d{2}-\d{2})", text)
            dob = dob_match.group(1) if dob_match else ""
            age = calculate_age(dob)
            exp = "Yes" if "Receptionist" in text or "Customer" in text else "No"
            eng_comp = "Yes" if "fluent in English" in text or "IELTS" in text or "TOEFL" in text else "No"
            qualifications = ", ".join(re.findall(r"(NVQ|Diploma|Degree|BIT)", text, re.IGNORECASE))

            shortlisted = (
                (ol_eng and ol_eng <= min_ol) and
                (al_eng and al_eng <= min_al) and
                (not require_exp or exp == "Yes") and
                (isinstance(age, int) and min_age <= age <= max_age)
            )

            results.append({
                "Name": name,
                "Age": age,
                "Gender": gender,
                "O/L English": ol_eng or "N/A",
                "A/L General English": al_eng or "N/A",
                "English Literature": eng_lit or "N/A",
                "English Competency": eng_comp,
                "Qualifications": qualifications or "N/A",
                "University": university or "N/A",
                "Town": town or "N/A",
                "Customer Service Exp": exp,
                "Shortlisted": "✅" if shortlisted else "❌"
            })

        df = pd.DataFrame(results)
        st.subheader("📋 CV Summary and Shortlisting")
        st.dataframe(df)

        st.subheader("📄 View Uploaded CVs")
        for name, file in cv_files.items():
            with st.expander(f"📂 {name}"):
                st.download_button(f"Download {name}", data=file.getvalue(), file_name=file.name)

        st.subheader("🗓️ Interview Tracking")
        for i, row in df[df["Shortlisted"] == "✅"].iterrows():
            st.markdown(f"### {row['Name']}")
            date = st.date_input(f"Interview Date - {row['Name']}", key=f"date_{i}")
            interviewer = st.selectbox(f"Select Interviewer - {row['Name']}", INTERVIEWERS, key=f"interviewer_{i}")
            outcome = st.selectbox(f"Outcome - {row['Name']}", ["Pending", "Pass", "Fail", "Selected", "Rejected"], key=f"outcome_{i}")
            notes = st.text_area(f"Notes - {row['Name']}", key=f"notes_{i}")
            interview_log.append({
                "Name": row['Name'],
                "Interview Date": date,
                "Interviewer": interviewer,
                "Outcome": outcome,
                "Notes": notes
            })

        if interview_log:
            st.subheader("📤 Export Interview Results")
            interview_df = pd.DataFrame(interview_log)
            buffer = BytesIO()
            interview_df.to_excel(buffer, index=False)
            st.download_button(label="Download Interview Tracker Excel", data=buffer.getvalue(), file_name="interview_tracking.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
