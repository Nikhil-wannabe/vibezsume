import streamlit as st
import streamlit_antd_components as sac
from streamlit_lottie import st_lottie
from streamlit_extras.add_vertical_space import add_vertical_space
import os
from typing import Optional, List, Dict, Any # For type hinting

# Assuming utils are in a directory accessible from pages, or PYTHONPATH is set
from utils.resume_parser import extract_text_from_pdf, extract_text_from_docx, parse_resume_text

# --- Constants ---
LOTTIE_LOADING_URL = "https://assets5.lottiefiles.com/packages/lf20_f9zrbfcs.json"
DATA_DIR = "data" # For temporary file storage

# --- Page Specific Session State Initialization ---
def _initialize_ra_state():
    """Initializes session state variables specific to the Resume Analyzer page."""
    # `resume_analysis_results` is initialized globally in app.py.
    # This page-specific init ensures it's at least an empty dict if page is directly loaded
    # and global init hasn't occurred or was cleared.
    if st.session_state.get('resume_analysis_results') is None:
        st.session_state.resume_analysis_results = {}

    if 'ra_uploaded_file_name' not in st.session_state:
        st.session_state.ra_uploaded_file_name = None
    if 'ra_raw_text' not in st.session_state:
        st.session_state.ra_raw_text = None

# --- Core Logic Functions ---
def _handle_file_upload(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> bool:
    """
    Handles the uploaded resume file: saves temporarily, extracts text, parses,
    and updates session state.

    Args:
        uploaded_file: The file object from st.file_uploader.

    Returns:
        True if processing was successful and new results are available, False otherwise.
    """
    new_file_processed = False
    # Process if it's a new file OR if results were cleared for some reason
    if st.session_state.ra_uploaded_file_name != uploaded_file.name or \
       not st.session_state.get('resume_analysis_results'): # Check if results are empty or None

        st.session_state.ra_uploaded_file_name = uploaded_file.name
        st.session_state.resume_analysis_results = {} # Clear previous results for a new file
        st.session_state.ra_raw_text = None

        loading_animation_container = st.empty()
        with loading_animation_container:
            try:
                st_lottie(LOTTIE_LOADING_URL, speed=1, loop=True, quality="medium",
                          height=100, width=100, key="ra_loading_lottie_widget") # Changed key
            except Exception as e:
                st.warning(f"Loading animation error: {e}")

        if not os.path.exists(DATA_DIR):
            try: os.makedirs(DATA_DIR)
            except OSError as e:
                st.error(f"Cannot create data directory: {e}. File processing aborted.")
                loading_animation_container.empty(); return False

        temp_file_path = os.path.join(DATA_DIR, uploaded_file.name)
        text: Optional[str] = None
        try:
            with open(temp_file_path, "wb") as f: f.write(uploaded_file.getbuffer())

            if uploaded_file.type == "application/pdf": text = extract_text_from_pdf(temp_file_path)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document": text = extract_text_from_docx(temp_file_path)
            st.session_state.ra_raw_text = text

        except Exception as e: st.error(f"Error reading or processing file: {e}")
        finally:
            if os.path.exists(temp_file_path):
                try: os.remove(temp_file_path)
                except OSError as e: st.warning(f"Could not remove temp file: {e}")
            loading_animation_container.empty()

        if text:
            st.success("Resume file processed successfully!")
            with st.spinner("Parsing resume content... This may take a moment."):
                parsed_data = parse_resume_text(text) # This can be time-consuming
                st.session_state.resume_analysis_results = parsed_data
                new_file_processed = True # Signal that new results are available
        elif uploaded_file: # File was uploaded, but text extraction failed
             st.error("Could not extract text. The file might be empty, corrupted, or a scanned image.")
        return new_file_processed
    return False # No new file was processed (e.g., same file, results already exist)

# --- UI Display Functions ---
def _display_personal_info(name: Optional[str], email: Optional[str], phone: Optional[str]):
    """Displays the personal information card if data is valid."""
    # Only display card if at least one piece of personal info is present and not "N/A"
    if (name and name != "N/A") or \
       (email and email != "N/A") or \
       (phone and phone != "N/A"):
        with st.container():
            st.markdown("<div class='info-card personal-info-card'>", unsafe_allow_html=True)
            st.markdown("<h4><span class='icon'>👤</span>Personal Information</h4>", unsafe_allow_html=True)
            if name and name != "N/A": st.markdown(f"<p><span class='icon'>📛</span><strong>Name:</strong> {name}</p>", unsafe_allow_html=True)
            if email and email != "N/A": st.markdown(f"<p><span class='icon'>✉️</span><strong>Email:</strong> {email}</p>", unsafe_allow_html=True)
            if phone and phone != "N/A": st.markdown(f"<p><span class='icon'>📞</span><strong>Phone:</strong> {phone}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        add_vertical_space(1)

def _display_skills_section(skills_list: List[str]):
    """Displays the skills section."""
    st.markdown("<h4 class='custom-h4'><span class='icon'>🛠️</span>Skills</h4>", unsafe_allow_html=True)
    valid_skills = [s for s in skills_list if s and s != "N/A"] # Filter out None or "N/A"
    if valid_skills:
        sac.tags([sac.Tag(label=skill, color='green', bordered=False) for skill in valid_skills],
                 align='start', size='md', key="ra_skills_tags_display") # Added key
    else:
        st.markdown("<p><em>(No skills extracted or provided.)</em></p>", unsafe_allow_html=True)
    add_vertical_space(1)

def _display_summary_section(summary_text: Optional[str]):
    """Displays the summary section."""
    st.markdown("<h4 class='custom-h4'><span class='icon'>📝</span>Summary</h4>", unsafe_allow_html=True)
    if summary_text and summary_text != "N/A":
        sac.alert(description=summary_text, color='cyan', banner=False, icon=True, closable=False, key="ra_summary_alert_display") # Added key
    else:
        st.markdown("<p><em>(No summary extracted or provided.)</em></p>", unsafe_allow_html=True)
    add_vertical_space(1)

def _display_education_section(education_list: List[Dict[str, str]]):
    """Displays education cards and their GSAP animation script."""
    st.markdown("<h4 class='custom-h4'><span class='icon'>🎓</span>Education</h4>", unsafe_allow_html=True)
    container_id = "education_cards_container_ra_page" # Page-specific ID
    st.markdown(f"<div id='{container_id}'>", unsafe_allow_html=True)

    meaningful_entries = [e for e in education_list if e.get('institution',"N/A") != "N/A" or e.get('degree',"N/A") != "N/A"]
    if meaningful_entries:
        for i, edu_entry in enumerate(meaningful_entries): # Use enumerate for unique keys
            with st.container():
                st.markdown(f"<div class='info-card education-card' id='edu-card-ra-{i}'>", unsafe_allow_html=True) # Unique card ID
                if edu_entry.get('degree',"N/A") != "N/A": st.markdown(f"<strong>{edu_entry['degree']}</strong>", unsafe_allow_html=True)
                if edu_entry.get('institution',"N/A") != "N/A": st.markdown(f"<p><span class='icon'>🏛️</span>Institution: {edu_entry['institution']}</p>", unsafe_allow_html=True)
                if edu_entry.get('date',"N/A") != "N/A": st.markdown(f"<p><span class='icon'>📅</span>Date: {edu_entry['date']}</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p><em>(No specific education details extracted.)</em></p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f"""<script>
        if (typeof gsap !== 'undefined' && document.getElementById('{container_id}')) {{
            gsap.from("#{container_id} .info-card", {{ duration: 0.5, autoAlpha: 0, y: 30, stagger: 0.15, ease: "power2.out" }});
        }}</script>""", unsafe_allow_html=True)
    add_vertical_space(1)

def _display_experience_section(experience_list: List[Dict[str, str]]):
    """Displays experience cards and their GSAP animation script."""
    st.markdown("<h4 class='custom-h4'><span class='icon'>👔</span>Experience</h4>", unsafe_allow_html=True)
    container_id = "experience_cards_container_ra_page" # Page-specific ID
    st.markdown(f"<div id='{container_id}'>", unsafe_allow_html=True)

    meaningful_entries = [e for e in experience_list if e.get('company',"N/A") != "N/A" or e.get('job_title',"N/A") != "N/A"]
    if meaningful_entries:
        for i, exp_entry in enumerate(meaningful_entries): # Use enumerate for unique keys
            with st.container():
                st.markdown(f"<div class='info-card experience-card' id='exp-card-ra-{i}'>", unsafe_allow_html=True) # Unique card ID
                if exp_entry.get('job_title',"N/A") != "N/A": st.markdown(f"<strong>{exp_entry['job_title']}</strong>", unsafe_allow_html=True)
                if exp_entry.get('company',"N/A") != "N/A": st.markdown(f"<p><span class='icon'>🏢</span>Company: {exp_entry['company']}</p>", unsafe_allow_html=True)
                if exp_entry.get('date_range',"N/A") != "N/A": st.markdown(f"<p><span class='icon'>📅</span>Dates: {exp_entry['date_range']}</p>", unsafe_allow_html=True)
                if exp_entry.get('description',"N/A") != "N/A": st.markdown(f"<div><strong>Responsibilities:</strong><br>{exp_entry['description']}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p><em>(No specific work experience details extracted.)</em></p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f"""<script>
        if (typeof gsap !== 'undefined' && document.getElementById('{container_id}')) {{
            gsap.from("#{container_id} .info-card", {{ duration: 0.5, autoAlpha: 0, y: 30, stagger: 0.15, ease: "power2.out" }});
        }}</script>""", unsafe_allow_html=True)
    add_vertical_space(1)

def _display_full_extracted_text(text_content: Optional[str]):
    """Displays the full extracted text in a collapsible expander if content exists."""
    if text_content:
        with st.expander("View Full Extracted Text (for debugging)", expanded=False):
            st.text_area("Full Extracted Text:", text_content, height=250, disabled=True, key="ra_full_text_display_widget") # Unique key

# --- Main Page Rendering Function ---
def render_resume_analyzer_page():
    """Main function to orchestrate the rendering of the Resume Analyzer page."""
    _initialize_ra_state()

    st.title("📝 Resume Analyzer")
    st.markdown("<p style='color: #cccccc;'>Upload your resume (PDF or DOCX) to extract and review its key components. Results will appear below.</p>", unsafe_allow_html=True)
    add_vertical_space(1)

    uploaded_file = st.file_uploader(
        "Upload your resume here:",
        type=["pdf", "docx"],
        key="ra_file_uploader_main_widget"
    )

    if uploaded_file:
        _handle_file_upload(uploaded_file)

    # Display results if they are present in session state
    # Ensure parsed_data is a dict, even if empty from a failed parse attempt
    parsed_data = st.session_state.get('resume_analysis_results', {})
    raw_text = st.session_state.get('ra_raw_text')

    if parsed_data: # If parsed_data is not None and not an empty dict (from failed parse)
        is_minimal = not parsed_data or (
            parsed_data.get("name", "N/A") == "N/A" and
            all(s == "N/A" or not s for s in parsed_data.get("skills", ["N/A"])) and # Check all skills are N/A or empty
            all(e.get('job_title', "N/A") == "N/A" and e.get('company', "N/A") == "N/A" for e in parsed_data.get("experience", [{'job_title':"N/A"}]))
        )

        # Show warning only if a file was processed, results are minimal, and some raw text was extracted (implies not a totally empty file)
        if uploaded_file and is_minimal and raw_text and st.session_state.ra_uploaded_file_name == uploaded_file.name:
             st.warning("Parsing was limited. The resume might be a scanned image, empty, or in an unusual format. Please review the 'Full Extracted Text' below if available.")

        results_container_id = "resume_results_display_main_container" # Unique ID
        st.markdown(f"<div class='fade-in' id='{results_container_id}'>", unsafe_allow_html=True)
        st.subheader("Parsed Resume Information:")

        _display_personal_info(parsed_data.get("name"), parsed_data.get("email"), parsed_data.get("phone"))
        _display_skills_section(parsed_data.get("skills", [])) # Pass empty list if skills not found
        _display_summary_section(parsed_data.get("summary"))
        _display_education_section(parsed_data.get("education", [])) # Pass empty list
        _display_experience_section(parsed_data.get("experience", [])) # Pass empty list

        # Show expander if raw_text exists, regardless of how minimal parsing was, for debugging.
        if raw_text:
            _display_full_extracted_text(raw_text)

        st.markdown("</div>", unsafe_allow_html=True)

    elif uploaded_file and not st.session_state.get('resume_analysis_results'):
        # This case covers if _handle_file_upload was called, but results are still None/empty
        # (e.g., an error message was already displayed by _handle_file_upload)
        pass

# --- Main execution call for the page ---
render_resume_analyzer_page()
