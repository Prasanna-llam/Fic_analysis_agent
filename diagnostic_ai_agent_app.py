import streamlit as st
import pandas as pd
from openai import OpenAI

# Load API key securely
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY is missing. Please add it to .streamlit/secrets.toml.")
    st.stop()

client = OpenAI(api_key=api_key)

def process_entry(complaint, issue_description):
    prompt = f"""You are an expert Automotive Diagnostic Engineer.

Your task is to:
1. Summarize the complaint and issue in 5 bullet points (~50 words).
2. Identify the diagnostic category from: [Diagnostic method NOK / Part failure / ECU replacement / Wiring harness / Reprogramming / Other]
3. If category is "Other", explain why in up to 50 words.

Complaint: {complaint}
Issue Description: {issue_description}

Return in this format:
Summary:
- ...
- ...
Category: ...
Reason (only if "Other"): ...
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# Streamlit UI
st.title("🔧 Automotive Diagnostic AI Agent")
st.write("Upload an Excel file containing 'Complaint' and 'Issue Description' columns.")

uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        if "Complaint" not in df.columns or "Issue Description" not in df.columns:
            st.error("❗ Required columns 'Complaint' and 'Issue Description' are missing.")
            st.stop()

        st.success("File uploaded successfully. Preview below:")
        st.dataframe(df[["Complaint", "Issue Description"]].head())

        if st.button("▶ Run Analysis"):
            st.info("Processing rows... please wait.")
            df["AI Output"] = df.apply(lambda row: process_entry(str(row["Complaint"]), str(row["Issue Description"])), axis=1)

            df[["Summary", "Category", "Reason (Other)"]] = df["AI Output"].str.extract(
                r"Summary:\s*(.*?)\s*Category:\s*(.*?)\s*Reason.*?:\s*(.*)", expand=True
            )

            st.success("✅ Analysis completed.")
            st.dataframe(df[["Summary", "Category", "Reason (Other)"]])

           out_path = "/mnt/data/AI_Diagnostic_Result.xlsx"
            df.to_excel(out_path, index=False)
            with open(out_path, "rb") as f:
                st.download_button("📥 Download Result File", f, file_name="AI_Diagnostic_Result.xlsx")

    except Exception as e:
        st.error(f"Error processing file: {e}")
