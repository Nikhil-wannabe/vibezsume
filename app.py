import streamlit as st
from utils.resume_parser import extract_text_from_pdf, extract_text_from_docx, parse_resume_text
import os

# Set page config
st.set_page_config(layout="wide", page_title="AI Resume Toolkit")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Resume Analyzer", "Job Analyzer", "Resume Builder"])

# Page content
if page == "Resume Analyzer":
    st.header("Resume Analyzer")
    uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
    if uploaded_file is not None:
        st.write("File uploaded successfully!")

        # Save uploaded file temporarily to parse
        # This is necessary because the parsing functions expect a file path
        temp_file_path = os.path.join("data", uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        text = None
        if uploaded_file.type == "application/pdf":
            text = extract_text_from_pdf(temp_file_path)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = extract_text_from_docx(temp_file_path)

        # Remove temporary file
        os.remove(temp_file_path)

        if text:
            st.subheader("Extracted Text (First 500 chars):")
            st.text_area("Text", text[:500], height=150)

            parsed_data = parse_resume_text(text)

            st.subheader("Parsed Resume Information:")
            if parsed_data.get("name"):
                st.write(f"**Name:** {parsed_data['name']}")
            if parsed_data.get("email"):
                st.write(f"**Email:** {parsed_data['email']}")
            if parsed_data.get("phone"):
                st.write(f"**Phone:** {parsed_data['phone']}")

            st.markdown("**Skills:**")
            if parsed_data.get("skills"):
                for skill in parsed_data["skills"]:
                    st.markdown(f"- {skill}")
            else:
                st.markdown("*(No skills extracted)*")

            st.markdown("**Summary:**")
            if parsed_data.get("summary"):
                st.markdown(parsed_data["summary"])
            else:
                st.markdown("*(No summary extracted)*")

            # Placeholders for other sections
            st.markdown("**Experience:** *(Placeholder - Not yet implemented)*")
            st.markdown("**Education:** *(Placeholder - Not yet implemented)*")

        else:
            st.error("Could not extract text from the uploaded file.")

elif page == "Job Analyzer":
    st.header("Job Analyzer")
    # Add content for Job Analyzer here
elif page == "Resume Builder":
    st.header("Resume Builder")
    # Add content for Resume Builder here

st.sidebar.markdown("---")
st.sidebar.markdown("Developed by [Your Name/Organization]")
st.sidebar.markdown("Powered by Streamlit")
