import streamlit as st
import streamlit_antd_components as sac # For sac.tags, sac.alert, sac.progress
from streamlit_lottie import st_lottie
from streamlit_extras.add_vertical_space import add_vertical_space
from typing import Dict, List, Optional, Set # For type hinting

# Assuming utils are in a directory accessible from pages, or PYTHONPATH is set
from utils.scraper import scrape_job_posting
from utils.job_analyzer import analyze_job_text

# --- Constants ---
LOTTIE_LOADING_URL: str = "https://assets5.lottiefiles.com/packages/lf20_f9zrbfcs.json"

# --- Page Specific Session State Initialization ---
def _initialize_ja_state():
    """
    Initializes session state variables specific to the Job Analyzer page if they don't exist.
    Global states like 'job_description_text' and 'job_analysis_results'
    are primarily initialized in app.py but this ensures they exist if this page is the entry point.
    """
    if 'job_description_text' not in st.session_state:
        st.session_state.job_description_text = ""
    if 'job_analysis_results' not in st.session_state:
        st.session_state.job_analysis_results = None
    # 'resume_analysis_results' is expected to be set by 01_Resume_Analyzer.py and read here.

# --- Core Logic Functions ---
def _handle_jd_input_and_analysis(job_url_input: str, job_text_area_input: str):
    """
    Handles input from URL or text area, triggers scraping if a URL is provided,
    then calls the text analysis function and updates session state.
    """
    st.session_state.job_description_text = ""  # Clear previous JD text
    st.session_state.job_analysis_results = None # Clear previous analysis results

    current_jd_text: str = "" # Initialize to empty string

    if job_url_input:
        loading_placeholder = st.empty()
        with loading_placeholder:
            try: # Attempt to show Lottie animation
                st_lottie(LOTTIE_LOADING_URL, speed=1, loop=True, quality="medium",
                          height=100, width=100, key="ja_lottie_scraping_widget")
            except Exception: # Fallback to spinner if Lottie fails
                with st.spinner(f"Scraping job description from {job_url_input}..."):
                    scraped_text = scrape_job_posting(job_url_input) # Perform the scraping

        # Ensure placeholder is cleared AFTER Lottie/spinner context
        if 'scraped_text' not in locals(): # If Lottie succeeded and spinner block was skipped
             with st.spinner(f"Scraping job description from {job_url_input}..."): # Show spinner explicitly
                scraped_text = scrape_job_posting(job_url_input)
        loading_placeholder.empty()


        if scraped_text.startswith("Error") or scraped_text.startswith("Could not"):
            st.error(scraped_text) # Display error message from scraper
        else:
            st.success("Job description scraped successfully!")
            current_jd_text = scraped_text
    elif job_text_area_input:
        st.info("Using pasted job description.")
        current_jd_text = job_text_area_input
    else:
        st.warning("Please provide either a Job Posting URL or Paste the Job Description text.")
        return # Exit if no valid input is provided

    st.session_state.job_description_text = current_jd_text # Store the obtained JD text

    if current_jd_text:
        with st.spinner("Analyzing job description content... This may take a moment."):
            analysis_results = analyze_job_text(current_jd_text)
            st.session_state.job_analysis_results = analysis_results
    # Streamlit's execution flow will automatically rerun, and the display functions will pick up the new state.

# --- UI Display Functions ---
def _display_job_description_text():
    """Displays the currently stored job description text in a collapsible expander."""
    if st.session_state.job_description_text: # Only display if text exists
        add_vertical_space(1)
        with st.expander("View Current Job Description", expanded=False):
            st.text_area(
                "Job Description Content:",
                st.session_state.job_description_text,
                height=300,
                disabled=True,
                key="ja_display_jd_text_area_widget" # Unique key for this widget
            )

def _display_job_analysis_results(results: Dict[str, Any]):
    """
    Displays the extracted key points (company, experience, skills) from the job description.
    Args:
        results: The dictionary returned by `analyze_job_text`.
    """
    st.markdown("<div class='fade-in'>", unsafe_allow_html=True) # For CSS fade-in animation
    st.markdown("<h4 class='custom-h4'><span class='icon'>📄</span>Job Description Key Points</h4>", unsafe_allow_html=True)

    company_name = results.get('company_name', "N/A")
    if company_name != "N/A":
        st.markdown(f"<strong><span class='icon'>🏢</span>Potential Company:</strong> {company_name}", unsafe_allow_html=True)
        add_vertical_space(1)

    seniority = results.get('seniority', "N/A")
    experience_years = results.get('experience_years', "N/A")
    exp_details: List[str] = []
    if seniority != "N/A": exp_details.append(f"Seniority: {seniority}")
    if experience_years != "N/A": exp_details.append(f"Years of Experience: {experience_years}")

    exp_info_html = "<strong><span class='icon'>📈</span>Experience Level:</strong> "
    exp_info_html += " | ".join(exp_details) if exp_details else "<em>(Not clearly specified or extracted)</em>"
    st.markdown(exp_info_html, unsafe_allow_html=True)
    add_vertical_space(1)

    skills: List[str] = results.get('skills', [])
    valid_skills = [s for s in skills if s and s != "N/A"]
    if valid_skills:
        st.markdown("<strong><span class='icon'>🛠️</span>Extracted Skills from Job Description:</strong>", unsafe_allow_html=True)
        sac.tags([sac.Tag(label=skill, color='blue', bordered=False) for skill in valid_skills],
                 align='start', size='md', key="ja_job_skills_tags") # Added key
    else:
        st.markdown("<strong><span class='icon'>🛠️</span>Extracted Skills:</strong> <em>(No specific skills extracted or skills listed as N/A.)</em>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True) # End .fade-in
    add_vertical_space(1)

def _display_resume_match_analysis(job_analysis_results: Dict[str, Any]):
    """
    Displays the skill comparison between the analyzed resume (from session state)
    and the provided job analysis results.
    Args:
        job_analysis_results: The dictionary from `analyze_job_text`.
    """
    st.markdown("---")
    st.markdown("<h4 class='custom-h4' style='color: #FFA500;'><span class='icon'>🎯</span>Resume Match Analysis</h4>", unsafe_allow_html=True)

    resume_data = st.session_state.get('resume_analysis_results')
    if not resume_data or not resume_data.get('skills') or resume_data.get('skills') == ["N/A"]:
        sac.alert(
            label='Resume Not Analyzed or No Skills in Resume',
            description='Please ensure your resume has been analyzed and contains skills in the "Resume Analyzer" tab. Then, re-analyze the job description here.',
            type='warning', icon=True, banner=True, key="ja_resume_alert"
        )
        return

    resume_skills: Set[str] = set(str(s).lower() for s in resume_data.get('skills', []) if s and s != "N/A")
    job_skills_list: List[str] = job_analysis_results.get('skills', [])
    job_skills: Set[str] = set(str(s).lower() for s in job_skills_list if s and s != "N/A")

    if not job_skills:
        st.markdown("<p><em>No skills were extracted from the job description to perform a match.</em></p>", unsafe_allow_html=True)
        return

    matching_skills = sorted(list(resume_skills.intersection(job_skills)))
    missing_skills = sorted(list(job_skills - resume_skills))
    additional_skills = sorted(list(resume_skills - job_skills))
    match_score = (len(matching_skills) / len(job_skills)) * 100 if job_skills else 0

    st.markdown(f"<h5>Skill Match Score: <span style='color: #4CAF50;'>{match_score:.2f}%</span></h5>", unsafe_allow_html=True)
    sac.progress(value=int(match_score), color='green', size='lg', striped=True,
                 description=f"{len(matching_skills)} of {len(job_skills)} job skills found in your resume.",
                 key="ja_match_progress")
    add_vertical_space(1)

    gsap_container_id = "ja_skill_match_results_container"
    st.markdown(f"<div id='{gsap_container_id}'>", unsafe_allow_html=True)
    item_class = "ja-skill-match-item"

    def _render_skill_tag_group(title: str, icon: str, skills_to_display: List[str], color: str, empty_message: str):
        st.markdown(f"<div class='{item_class}'><strong><span class='icon'>{icon}</span>{title}:</strong>", unsafe_allow_html=True)
        if skills_to_display:
            sac.tags([sac.Tag(label=s.capitalize(), color=color) for s in skills_to_display], size='sm', key=f"tags_{title.replace(' ','_').lower()}")
        else:
            st.markdown(f"<p><em>{empty_message}</em></p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        add_vertical_space(1)

    _render_skill_tag_group("Matching Skills", "✅", matching_skills, "green", "No direct skill matches found.")
    _render_skill_tag_group("Missing Skills (In JD, not Resume)", "❌", missing_skills, "red", "All job skills appear to be covered in your resume!")
    _render_skill_tag_group("Additional Skills (In Resume, not JD)", "➕", additional_skills, "geekblue", "No additional skills noted in resume compared to this job description.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <script>
        if (typeof gsap !== 'undefined' && document.getElementById('{gsap_container_id}')) {{
            setTimeout(function() {{
                gsap.from("#{gsap_container_id} .{item_class}", {{
                    duration: 0.5, autoAlpha: 0, y: 30, stagger: 0.15, ease: "power2.out"
                }});
            }}, 150);
        }}
    </script>""", unsafe_allow_html=True)

# --- Main Page Rendering Function ---
def render_job_analyzer_page():
    """Main function to orchestrate the rendering of the Job Analyzer page."""
    _initialize_ja_state()

    st.title("🔍 Job Analyzer")
    st.markdown(
        "<p style='color: #cccccc;'>Enter a job description URL or paste the text directly. "
        "The tool will extract key information and compare required skills against your analyzed resume.</p>",
        unsafe_allow_html=True
    )
    add_vertical_space(1)

    job_url_input = st.text_input("Job Posting URL (Optional)", placeholder="https://www.example.com/job/123", key="ja_url_input_field")
    job_text_area_input = st.text_area("Or Paste Job Description Here", height=250,
                                       placeholder="Paste the full job description text here...", key="ja_text_area_field")

    if st.button("Analyze Job Description", key="ja_analyze_jd_main_btn"): # More specific key
        _handle_jd_input_and_analysis(job_url_input, job_text_area_input)

    _display_job_description_text()

    job_analysis_data = st.session_state.get('job_analysis_results')
    if job_analysis_data:
        _display_job_analysis_results(job_analysis_data)
        _display_resume_match_analysis(job_analysis_data)
    elif st.session_state.get('job_description_text') and not job_analysis_data:
        st.warning(
            "Job description was processed, but no specific analysis results to display (e.g., skills, experience). "
            "The job text might be too short, unclear, or an error occurred during detailed analysis."
        )

# --- Main execution call for the page ---
render_job_analyzer_page()
