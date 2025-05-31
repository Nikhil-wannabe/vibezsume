import streamlit as st
import streamlit_antd_components as sac # Import Antd Components
from streamlit_lottie import st_lottie # Import Lottie for animations
from streamlit_extras.add_vertical_space import add_vertical_space # For spacing
from utils.resume_parser import extract_text_from_pdf, extract_text_from_docx, parse_resume_text
from utils.scraper import scrape_job_posting
from utils.job_analyzer import analyze_job_text
from utils import pdf_templates # Import PDF generation utilities
import os
import time
import json # For loading predefined_options.json
import io # For PDF in-memory buffer

# Set page config - Using "wide" layout and a dark theme by default from Streamlit's options
st.set_page_config(layout="wide", page_title="AI Resume Toolkit", initial_sidebar_state="expanded")

# --- GSAP Library (Load Once) ---
# Using a more recent version of GSAP if available, ensure it's a valid CDN link.
# The example used 3.12.2. If newer, like 3.12.5, use that.
# For stability in this environment, I'll stick to a known version.
st.markdown("""
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
""", unsafe_allow_html=True)


# --- Custom CSS ---
# (No changes to CSS content itself in this step, just ensuring GSAP is loaded before it)
custom_css = """
<style>
    /* Base theme colors - Dark */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; /* Modern sans-serif font */
        color: #e0e0e0; /* Light grey text */
        background-color: #1a1a1a; /* Dark background */
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff; /* White headings */
    }

    /* Sidebar styling */
    .stSidebar {
        background-color: #262626; /* Slightly lighter dark for sidebar */
        padding: 1rem;
    }
    .stSidebar .sidebar-content {
         padding-top: 1rem;
    }
    /* Custom styles for sac.menu - ensure it's below general sidebar style if overriding */
    .ant-menu-dark.ant-menu-inline-collapsed > .ant-menu-item,
    .ant-menu-dark.ant-menu-inline-collapsed > .ant-menu-submenu > .ant-menu-submenu-title,
    .ant-menu-dark > .ant-menu-item > .ant-menu-title-content,
    .ant-menu-dark > .ant-menu-submenu > .ant-menu-submenu-title > .ant-menu-title-content {
        color: #e0e0e0; /* Light grey text for menu items */
    }
    .ant-menu-dark .ant-menu-item-selected {
        background-color: #4CAF50 !important; /* Green for selected item */
        color: #ffffff !important;
    }
    .ant-menu-dark .ant-menu-item:hover,
    .ant-menu-dark .ant-menu-submenu-title:hover {
        background-color: #333333 !important; /* Hover effect */
        color: #ffffff !important;
    }
    .ant-menu-dark .ant-menu-item-selected .anticon,
    .ant-menu-dark .ant-menu-item-selected .ant-menu-title-content {
        color: #ffffff !important; /* Ensure icon and text are white on selection */
    }
    .anticon { /* Icon styling */
        font-size: 18px !important;
        margin-right: 10px !important;
    }

    /* Button styling */
    .stButton>button {
        border: 2px solid #4CAF50;
        background-color: transparent;
        color: #4CAF50;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 8px;
        transition-duration: 0.4s;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #4CAF50;
        color: white;
    }

    /* File uploader styling */
    .stFileUploader label {
        color: #e0e0e0 !important; /* Lighter label text */
    }
    .stFileUploader > div > button { /* The 'Browse files' button */
        border: 1px solid #4CAF50;
        background-color: #2a2a2a;
        color: #e0e0e0;
        border-radius: 5px;
    }
    .stFileUploader > div > button:hover {
        background-color: #3a3a3a;
        border-color: #5cb85c;
    }

    /* Text input / Text area */
    .stTextInput > div > div > input, .stTextArea > div > textarea {
        background-color: #2a2a2a;
        color: #e0e0e0;
        border: 1px solid #444;
        border-radius: 5px;
    }
    .stTextInput > label, .stTextArea > label {
        color: #e0e0e0 !important;
    }

    /* Markdown & general text */
    p, .stMarkdown, .stWrite {
        color: #cccccc; /* Slightly dimmer than primary text for readability */
    }

    /* Improve spacing for uploaded file info */
    .stAlert { /* This is where "File uploaded successfully!" appears */
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    /* Fade-in animation for results */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeIn 0.5s ease-out forwards;
    }

    /* Custom card style for personal info */
    .info-card {
        background-color: #2a2a2a;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #3a3a3a;
        margin-bottom: 10px;
    }
    .info-card h4 {
        margin-bottom: 10px;
        color: #4CAF50; /* Green accent for card titles */
    }
    .info-card p {
        margin-bottom: 5px;
        color: #e0e0e0;
    }
    .info-card .icon {
        margin-right: 8px;
        color: #4CAF50; /* Green icons */
    }

    /* Style for custom markdown H4 titles to match info-card title */
    .custom-h4 {
        color: #4CAF50; /* Green accent */
        font-size: 1.25em; /* Standard h4 size, adjust if needed */
        margin-top: 1.5rem; /* Add some space above these titles */
        margin-bottom: 0.75rem;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Lottie animation URLs
LOTTIE_LOADING_URL = "https://assets5.lottiefiles.com/packages/lf20_f9zrbfcs.json" # Example loading spinner
# LOTTIE_SIDEBAR_URL = "https://assets2.lottiefiles.com/packages/lf20_XyHNoj.json" # Example abstract/tech animation - Replaced with a more subtle one
LOTTIE_SIDEBAR_URL = "https://assetslottiefiles.com/packages/lf20_CgY9IR7yC9.json" # A more subtle, abstract geometric animation
# Sidebar navigation using streamlit-antd-components
with st.sidebar:
    st.title("AI Resume Toolkit")
    try:
        st_lottie(LOTTIE_SIDEBAR_URL, speed=1, reverse=False, loop=True, quality="low", height=120, width=220, key="sidebar_lottie_main")
    except Exception as e:
        st.error(f"Lottie Error: {e}") # Display error if Lottie fails to load
    add_vertical_space(1)

    page = sac.menu([
        sac.MenuItem('Resume Analyzer', icon='file-text'),
        sac.MenuItem('Job Analyzer', icon='search'),
        sac.MenuItem('Resume Builder', icon='tools'),
        sac.MenuItem(type='divider'),
        sac.MenuItem('Settings', icon='gear', children=[
            sac.MenuItem('Account', icon='user'),
            sac.MenuItem('Preferences', icon='sliders'),
        ]),
    ], format_func='title', open_all=False, index=0, return_index=False)

    add_vertical_space(2)
    st.markdown("---")
    st.markdown("Developed by AI Resume Toolkit Team")
    st.markdown("Powered by Streamlit & Friends")

# Page content
# To keep it simple, we'll use the label of the menu item directly.
# Ensure these labels match the ones in sac.menu
if page == "Resume Analyzer":
    st.header("Resume Analyzer")
    uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

    if uploaded_file is not None:
        # Display loading animation while processing
        with st.spinner("Processing your resume..."): # Using st.spinner as a simple alternative
            # Alternative with Lottie:
            loading_animation_container = st.empty()
            with loading_animation_container:
                try:
                    st_lottie(LOTTIE_LOADING_URL, speed=1, loop=True, quality="medium", height=100, width=100, key="loading_lottie_main")
                except Exception as e:
                    st.warning("Loading animation could not be displayed.") # Non-critical, so use warning

            time.sleep(2) # Simulate processing time

            # Save uploaded file temporarily to parse
            temp_file_path = os.path.join("data", uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            text = None
            if uploaded_file.type == "application/pdf":
                text = extract_text_from_pdf(temp_file_path)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = extract_text_from_docx(temp_file_path)

            os.remove(temp_file_path) # Remove temporary file

            loading_animation_container.empty() # Clear Lottie animation

        if text:
            st.success("Resume processed successfully!")
            add_vertical_space(1)

            # Animate the display of parsed data (simple fade-in using CSS)
            # To do this properly with individual elements, each would need to be wrapped.
            # For now, wrapping the whole results section.
            # The fade-in class is a generic CSS animation. GSAP will be used for card-specific staggers.
            st.markdown("<div class='fade-in' id='resume_results_container'>", unsafe_allow_html=True)

            parsed_data = parse_resume_text(text)
            st.session_state.resume_analysis_results = parsed_data # Store in session state

            # Check if parsing yielded minimal results and show a warning if so
            if parsed_data.get("name", "N/A") == "N/A" and \
               (not parsed_data.get("skills") or parsed_data.get("skills") == ["N/A"]) and \
               (not parsed_data.get("experience") or not any(e.get('job_title') != "N/A" for e in parsed_data.get("experience",[]))):
                st.warning("Parsing was limited. The resume might be a scanned image, empty, or in an unusual format. Please check the content if results are not as expected.")

            # Displaying Parsed Information with enhanced styling
            st.subheader("Parsed Resume Information:")

            # Personal Information Card
            with st.container():
                st.markdown("""
                <div class="info-card">
                    <h4><span class="icon">👤</span>Personal Information</h4>
                """, unsafe_allow_html=True)
                if parsed_data.get("name"):
                    st.markdown(f"""<p><span class="icon">📛</span><strong>Name:</strong> {parsed_data['name']}</p>""", unsafe_allow_html=True)
                if parsed_data.get("email"):
                    st.markdown(f"""<p><span class="icon">✉️</span><strong>Email:</strong> {parsed_data['email']}</p>""", unsafe_allow_html=True)
                if parsed_data.get("phone"):
                    st.markdown(f"""<p><span class="icon">📞</span><strong>Phone:</strong> {parsed_data['phone']}</p>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            add_vertical_space(1)

            # Skills Section
            if parsed_data.get("skills"):
                st.markdown("<h4 class='custom-h4'><span class='icon'>🛠️</span>Skills</h4>", unsafe_allow_html=True)
                # Using sac.tags for skills
                sac.tags([sac.Tag(label=skill, color='green', bordered=False) for skill in parsed_data["skills"]],
                         format_func=None, align='start', size='md')
            else:
                st.markdown("<p><em>(No skills extracted)</em></p>", unsafe_allow_html=True)

            add_vertical_space(1)

            # Summary Section
            if parsed_data.get("summary"):
                st.markdown("<h4 class='custom-h4'><span class='icon'>📝</span>Summary</h4>", unsafe_allow_html=True)
                sac.alert(description=parsed_data["summary"], color='cyan', banner=False, icon=True, closable=False)
            else:
                st.markdown("<p><em>(No summary extracted)</em></p>", unsafe_allow_html=True)

            add_vertical_space(1)

            # Extracted Text (collapsible)
            with st.expander("View Extracted Text (First 500 chars)", expanded=False):
                st.text_area("Full Extracted Text", text[:500], height=150, disabled=True)

            # Education Section
            st.markdown("<h4 class='custom-h4'><span class='icon'>🎓</span>Education</h4>", unsafe_allow_html=True)
            st.markdown("<div id='education_cards_container'>", unsafe_allow_html=True) # GSAP Target Wrapper
            if parsed_data.get("education"):
                for i, edu_entry in enumerate(parsed_data["education"]): # Added index for unique keys if needed later
                    if edu_entry.get('institution') != "N/A":
                        with st.container():
                            # Each card could have a more unique class if needed: class='info-card education-card'
                            st.markdown(f"<div class='info-card'>", unsafe_allow_html=True)
                            if edu_entry.get('degree') and edu_entry.get('degree') != "N/A":
                                st.markdown(f"<strong>{edu_entry['degree']}</strong>", unsafe_allow_html=True)
                            if edu_entry.get('institution') and edu_entry.get('institution') != "N/A":
                                st.markdown(f"<p><span class='icon'>🏛️</span>Institution: {edu_entry['institution']}</p>", unsafe_allow_html=True)
                            if edu_entry.get('date') and edu_entry.get('date') != "N/A":
                                st.markdown(f"<p><span class='icon'>📅</span>Date: {edu_entry['date']}</p>", unsafe_allow_html=True)
                            st.markdown(f"</div>", unsafe_allow_html=True)
                        add_vertical_space(1) # This spacer might interfere with clean stagger if not part of the card itself
                    elif len(parsed_data["education"]) == 1 :
                         st.markdown("<p><em>(No specific education details extracted or provided in a parsable format.)</em></p>", unsafe_allow_html=True)
            else:
                st.markdown("<p><em>(No education details extracted)</em></p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True) # End education_cards_container
            st.markdown("""
            <script>
                // Ensure GSAP is loaded before running this
                if (typeof gsap !== 'undefined') {
                    gsap.from("#education_cards_container .info-card", {
                        duration: 0.5,
                        autoAlpha: 0, // handles opacity and visibility
                        y: 50,
                        stagger: 0.2,
                        ease: "power2.out"
                    });
                }
            </script>
            """, unsafe_allow_html=True)
            add_vertical_space(1)

            # Experience Section
            st.markdown("<h4 class='custom-h4'><span class='icon'>👔</span>Experience</h4>", unsafe_allow_html=True)
            st.markdown("<div id='experience_cards_container'>", unsafe_allow_html=True) # GSAP Target Wrapper
            if parsed_data.get("experience"):
                for i, exp_entry in enumerate(parsed_data["experience"]): # Added index
                    if exp_entry.get('company') != "N/A":
                        with st.container():
                            st.markdown(f"<div class='info-card'>", unsafe_allow_html=True)
                            if exp_entry.get('job_title') and exp_entry.get('job_title') != "N/A":
                                st.markdown(f"<strong>{exp_entry['job_title']}</strong>", unsafe_allow_html=True)
                            if exp_entry.get('company') and exp_entry.get('company') != "N/A":
                                st.markdown(f"<p><span class='icon'>🏢</span>Company: {exp_entry['company']}</p>", unsafe_allow_html=True)
                            if exp_entry.get('date_range') and exp_entry.get('date_range') != "N/A":
                                st.markdown(f"<p><span class='icon'>📅</span>Dates: {exp_entry['date_range']}</p>", unsafe_allow_html=True)
                            if exp_entry.get('description') and exp_entry.get('description') != "N/A":
                                st.markdown(f"<div><strong>Responsibilities:</strong><br>{exp_entry['description']}</div>", unsafe_allow_html=True)
                            st.markdown(f"</div>", unsafe_allow_html=True)
                        add_vertical_space(1) # Spacer might affect stagger visuals
                    elif len(parsed_data["experience"]) == 1:
                        st.markdown("<p><em>(No specific work experience details extracted or provided in a parsable format.)</em></p>", unsafe_allow_html=True)
            else:
                st.markdown("<p><em>(No work experience details extracted)</em></p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True) # End experience_cards_container
            st.markdown("""
            <script>
                if (typeof gsap !== 'undefined') {
                    gsap.from("#experience_cards_container .info-card", {
                        duration: 0.5,
                        autoAlpha: 0,
                        y: 50,
                        stagger: 0.2,
                        ease: "power2.out"
                    });
                }
            </script>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True) # End of main fade-in results_container (if used) or general fade-in.

        else:
            st.error("Could not extract text from the uploaded file. Please ensure it's a valid PDF or DOCX.")

elif page == "Job Analyzer":
    st.header("Job Analyzer")
    st.markdown("<p style='color: #cccccc;'>Enter a job description URL or paste the text directly to analyze it against your resume.</p>", unsafe_allow_html=True)
    add_vertical_space(1)

    job_url = st.text_input("Job Posting URL (Optional)", placeholder="https://www.example.com/job/123")
    job_text_area = st.text_area("Or Paste Job Description Here", height=250, placeholder="Paste the full job description here...")

    # Initialize session state for job_description if it doesn't exist
    if 'job_description_text' not in st.session_state:
        st.session_state.job_description_text = ""
    if 'job_analysis_results' not in st.session_state:
        st.session_state.job_analysis_results = None

    if st.button("Analyze Job Description", key="analyze_jd_button"):
        st.session_state.job_description_text = "" # Clear previous text
        st.session_state.job_analysis_results = None # Clear previous results

        current_jd_text = ""
        if job_url:
            with st.spinner(f"Scraping job description from {job_url}..."):
                scraped_text = scrape_job_posting(job_url)
                if scraped_text.startswith("Error fetching URL:") or scraped_text.startswith("Could not automatically extract"):
                    st.error(scraped_text)
                else:
                    st.success("Job description scraped successfully!")
                    current_jd_text = scraped_text
        elif job_text_area:
            st.info("Using pasted job description.")
            current_jd_text = job_text_area
        else:
            st.warning("Please provide a URL or paste the job description text.")
            current_jd_text = "" # Ensure it's empty if no input

        st.session_state.job_description_text = current_jd_text

        if current_jd_text:
            with st.spinner("Analyzing job description text..."):
                analysis_results = analyze_job_text(current_jd_text)
                st.session_state.job_analysis_results = analysis_results
                # The results will be displayed below, outside this button block, based on session_state

    # Display the processed job description if available in session state
    if st.session_state.job_description_text:
        add_vertical_space(1)
        with st.expander("View Current Job Description", expanded=False): # Default to collapsed
            st.text_area("Job Description Content", st.session_state.job_description_text, height=300, disabled=True, key="jd_display_area")

    # Display analysis results if available
    if st.session_state.get('job_analysis_results'): # Use .get for safer access
        results = st.session_state.job_analysis_results
        st.markdown("<h4 class='custom-h4'><span class='icon'>🔍</span>Job Description Analysis</h4>", unsafe_allow_html=True)

        # Display Skills from Job Analysis
        if results.get('skills') and results['skills'] != ["N/A"]:
            st.markdown("<strong><span class='icon'>🛠️</span>Extracted Skills:</strong>", unsafe_allow_html=True)
            sac.tags([sac.Tag(label=skill, color='blue', bordered=False) for skill in results['skills']],
                     format_func=None, align='start', size='md')
            add_vertical_space(1)
        else:
            st.markdown("<strong><span class='icon'>🛠️</span>Extracted Skills:</strong> <p><em>(No specific skills found or extracted)</em></p>", unsafe_allow_html=True)

        # Display Experience Level
        exp_info_html = "<strong><span class='icon'>📈</span>Experience Level:</strong> "
        exp_details = []
        if results.get('seniority') and results['seniority'] != "N/A":
            exp_details.append(f"Seniority: {results['seniority']}")
        if results.get('experience_years') and results['experience_years'] != "N/A":
            exp_details.append(f"Years: {results['experience_years']}")

        if exp_details:
            exp_info_html += " | ".join(exp_details)
        else:
            exp_info_html += "<p><em>(No specific experience level information extracted)</em></p>"
        st.markdown(exp_info_html, unsafe_allow_html=True)
        add_vertical_space(1)

        # Display Company Name (if found)
        if results.get('company_name') and results['company_name'] != "N/A":
            st.markdown(f"<strong><span class='icon'>🏢</span>Potential Company:</strong> {results['company_name']}", unsafe_allow_html=True)
            add_vertical_space(1)

        # Placeholder for actual matching against resume (Next Step) -> This is where we implement it
        st.markdown("---")
        # st.markdown("<h5 class='custom-h4' style='color: #FFA500;'><span class='icon'>🎯</span>Resume Matching (Coming Next)</h5>", unsafe_allow_html=True) # Orange color for next step
        # sac.alert(label='Next Up', description='The next step will be to compare these extracted job details with your uploaded resume.',
        #           type='info', icon=True)

        # --- Resume Match Analysis Implementation ---
        # Ensure this container is only added if there are results to show, to prevent empty div with GSAP target
        if 'resume_analysis_results' in st.session_state and st.session_state.resume_analysis_results and \
           st.session_state.job_analysis_results.get('skills') and \
           st.session_state.job_analysis_results['skills'] != ["N/A"]:
            st.markdown("<div id='skill_match_cards_container'>", unsafe_allow_html=True) # GSAP Target Wrapper

        st.markdown("<h4 class='custom-h4' style='color: #FFA500;'><span class='icon'>🎯</span>Resume Match Analysis</h4>", unsafe_allow_html=True)

        if 'resume_analysis_results' not in st.session_state or not st.session_state.get('resume_analysis_results'): # Check .get for safety
            sac.alert(label='Resume Not Analyzed',
                      description='Please analyze your resume first in the "Resume Analyzer" tab to see the match results, then re-analyze the job description.',
                      type='warning', icon=True)
        else:
            resume_skills_raw = st.session_state.resume_analysis_results.get('skills', [])
            # Ensure resume skills are lowercase for comparison, as job skills are from a predefined list (mostly lowercase)
            # and then capitalized for display. For comparison, consistency is key.
            resume_skills = set([str(skill).lower() for skill in resume_skills_raw if skill != "N/A"])

            job_skills_raw = results.get('skills', [])
            job_skills = set([str(skill).lower() for skill in job_skills_raw if skill != "N/A"])

            if not job_skills:
                st.markdown("<p><em>No skills were extracted from the job description to compare.</em></p>", unsafe_allow_html=True)
            else:
                matching_skills = sorted(list(resume_skills.intersection(job_skills)))
                missing_skills = sorted(list(job_skills - resume_skills))
                additional_skills_in_resume = sorted(list(resume_skills - job_skills))

                match_score = 0
                if job_skills: # Avoid division by zero
                    match_score = (len(matching_skills) / len(job_skills)) * 100 if job_skills else 0

                st.markdown(f"<h5>Skill Match Score: {match_score:.2f}%</h5>", unsafe_allow_html=True)
                sac.progress(value=int(match_score), color='green', size='lg', striped=True)
                add_vertical_space(1)

                # These will be animated as blocks
                if matching_skills:
                    st.markdown("<div class='skill-match-block'><strong><span class='icon'>✅</span>Matching Skills:</strong>", unsafe_allow_html=True)
                    sac.tags([sac.Tag(label=skill.capitalize(), color='green', bordered=False) for skill in matching_skills],
                             format_func=None, align='start', size='sm')
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='skill-match-block'><strong><span class='icon'>✅</span>Matching Skills:</strong> <p><em>No direct skill matches found.</em></p></div>", unsafe_allow_html=True)
                add_vertical_space(1)

                if missing_skills:
                    st.markdown("<div class='skill-match-block'><strong><span class='icon'>❌</span>Missing Skills (Job requirements not in your resume):</strong>", unsafe_allow_html=True)
                    sac.tags([sac.Tag(label=skill.capitalize(), color='red', bordered=False) for skill in missing_skills],
                             format_func=None, align='start', size='sm')
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='skill-match-block'><strong><span class='icon'>❌</span>Missing Skills:</strong> <p><em>Your resume appears to cover all skills listed in the job description!</em></p></div>", unsafe_allow_html=True)
                add_vertical_space(1)

                if additional_skills_in_resume:
                    st.markdown("<div class='skill-match-block'><strong><span class='icon'>➕</span>Additional Skills (In your resume, not in job description):</strong>", unsafe_allow_html=True)
                    sac.tags([sac.Tag(label=skill.capitalize(), color='geekblue', bordered=False) for skill in additional_skills_in_resume],
                             format_func=None, align='start', size='sm')
                    st.markdown("</div>", unsafe_allow_html=True)
                # else: (No message if no additional skills, to keep UI cleaner)

        # Close the skill_match_cards_container div only if it was opened
        if 'resume_analysis_results' in st.session_state and st.session_state.resume_analysis_results and \
           st.session_state.job_analysis_results.get('skills') and \
           st.session_state.job_analysis_results['skills'] != ["N/A"]:
            st.markdown("</div>", unsafe_allow_html=True) # End skill_match_cards_container
            st.markdown("""
            <script>
    if (typeof gsap !== 'undefined') {
        // Delay slightly to ensure elements are in DOM from Streamlit's rendering pass
        setTimeout(function() {
            gsap.from("#skill_match_cards_container .skill-match-block", {
                duration: 0.5,
                autoAlpha: 0,
                y: 30,
                stagger: 0.15,
                ease: "power2.out"
            });
        }, 100); // 100ms delay, adjust if needed
    }
</script>
            """, unsafe_allow_html=True)
            if (typeof gsap !== 'undefined') {
                // Delay slightly to ensure elements are in DOM from Streamlit's rendering pass
                setTimeout(function() {
                    gsap.from("#skill_match_cards_container .skill-match-block", {
                        duration: 0.5,
                        autoAlpha: 0,
                        y: 30,
                        stagger: 0.15,
                        ease: "power2.out"
                    });
                }, 100); // 100ms delay, adjust if needed
            }
        </script>
        """, unsafe_allow_html=True)


elif page == "Resume Builder":
    st.header("Resume Builder")
    st.markdown("<p style='color: #cccccc;'>Build your professional resume step-by-step.</p>", unsafe_allow_html=True)
    add_vertical_space(1)

    # --- Function to Reset Resume Builder State ---
    def reset_resume_builder_state():
        rb_fields_defaults = {
            'rb_name': '', 'rb_email': '', 'rb_phone': '', 'rb_linkedin': '', 'rb_portfolio': '',
            'rb_summary': '',
            'rb_experience': [],
            'rb_education': [],
            'rb_skills': [],
            'rb_projects': [],
            'rb_awards': []
        }
        for field, default_value in rb_fields_defaults.items():
            st.session_state[field] = default_value
        st.session_state.rb_step_index = 0
        # st.session_state.current_rb_step = 0 # If you were using this one
        st.toast("Resume Builder data cleared!", icon="🗑️")

    # --- Initialize Session State for Resume Builder (if not already done by reset) ---
    # This ensures that if the page is loaded for the first time and not via a reset,
    # the keys still get initialized.
    initial_rb_fields = {
        'rb_name': '', 'rb_email': '', 'rb_phone': '', 'rb_linkedin': '', 'rb_portfolio': '',
        'rb_summary': '', 'rb_experience': [], 'rb_education': [], 'rb_skills': [],
        'rb_projects': [], 'rb_awards': []
    }
    for field, default_value in initial_rb_fields.items():
        if field not in st.session_state:
            st.session_state[field] = default_value

    if 'rb_step_index' not in st.session_state: # Separate from current_rb_step if that was used differently
        st.session_state.rb_step_index = 0

    # --- "Start Over" Button ---
    # Placed near the top for easy access
    if st.button("🗑️ Start Over / Clear All Data", key="rb_clear_all_button", type="secondary"):
        reset_resume_builder_state()
        st.rerun() # Rerun to reflect cleared state immediately


    # --- Load Predefined Options ---
    try:
        with open("data/predefined_options.json", "r") as f:
            predefined_options = json.load(f)
        common_skills_options = predefined_options.get("common_skills", {})
        action_verbs = predefined_options.get("action_verbs", [])
    except FileNotFoundError:
        st.error("Error: `data/predefined_options.json` not found. Skill suggestions will be limited.")
        common_skills_options = {}
        action_verbs = []


    # --- Steps Navigation ---
    steps_items = [
        sac.StepsItem(title='Personal Info', icon='person-badge'),
        sac.StepsItem(title='Summary', icon='text-paragraph'),
        sac.StepsItem(title='Experience', icon='briefcase'),
        sac.StepsItem(title='Education', icon='book'),
        sac.StepsItem(title='Skills', icon='tools'),
        sac.StepsItem(title='Projects', icon='kanban'),
        sac.StepsItem(title='Awards', icon='award'),
        sac.StepsItem(title='Review & Download', icon='cloud-download')
    ]

    # Use st.session_state to keep track of the current step index
    # This is crucial because sac.steps is stateless by default if `index` is not managed
    if 'rb_step_index' not in st.session_state:
        st.session_state.rb_step_index = 0

    # Update current_rb_step based on sac.steps interaction
    # The component itself doesn't directly set session_state, so we manage it
    # We use a different key for the component's current selection to avoid direct loop
    # if 'sac_steps_current' not in st.session_state:
    #     st.session_state.sac_steps_current = st.session_state.rb_step_index

    # selected_step_title = sac.steps(
    #     items=steps_items,
    #     index=st.session_state.rb_step_index, # Control current step with session state
    #     format_func='title',
    #     placement='horizontal',
    #     size='default',
    #     direction='horizontal',
    #     type='default', # 'default', 'navigation', 'tabs'
    #     dot=False,
    #     return_index=True, # Get index back
    #     key="resume_builder_steps"
    # )
    # st.session_state.rb_step_index = selected_step_title # Update session state with the returned index

    # Simpler way to manage step state without immediate callback complexity for now:
    # Use columns for Prev/Next buttons to control step

    current_step_index = st.session_state.get('rb_step_index', 0)

    sac.steps(
        items=steps_items,
        index=current_step_index,
        format_func='title',
        placement='horizontal',
        readonly=True, # Make steps display-only, control with buttons
        key="rb_steps_display"
    )
    add_vertical_space(2)

    # --- Form for Each Step ---
    if current_step_index == 0: # Personal Information
        st.markdown("<h4 class='custom-h4'>Personal Information</h4>", unsafe_allow_html=True)
        st.session_state.rb_name = st.text_input("Full Name", value=st.session_state.rb_name, key="rb_name_input")
        cols = st.columns(2)
        with cols[0]:
            st.session_state.rb_email = st.text_input("Email Address", value=st.session_state.rb_email, key="rb_email_input")
            st.session_state.rb_linkedin = st.text_input("LinkedIn Profile URL (Optional)", value=st.session_state.rb_linkedin, key="rb_linkedin_input")
        with cols[1]:
            st.session_state.rb_phone = st.text_input("Phone Number", value=st.session_state.rb_phone, key="rb_phone_input")
            st.session_state.rb_portfolio = st.text_input("Portfolio/Website URL (Optional)", value=st.session_state.rb_portfolio, key="rb_portfolio_input")

    elif current_step_index == 1: # Summary/Objective
        st.markdown("<h4 class='custom-h4'>Summary / Objective</h4>", unsafe_allow_html=True)
        st.session_state.rb_summary = st.text_area(
            "Write a brief summary or objective (2-4 sentences)",
            value=st.session_state.rb_summary,
            height=150,
            key="rb_summary_input"
        )
        st.markdown(f"<small style='color: #cccccc;'>{len(st.session_state.rb_summary.split())} words</small>", unsafe_allow_html=True)


    elif current_step_index == 2: # Work Experience
        st.markdown("<h4 class='custom-h4'>Work Experience</h4>", unsafe_allow_html=True)

        # Display existing experience entries
        for i, exp in enumerate(st.session_state.rb_experience):
            with st.expander(f"Experience {i+1}: {exp.get('job_title', 'New Entry')}", expanded=True):
                exp['job_title'] = st.text_input(f"Job Title##{i}", value=exp.get('job_title', ''), key=f"rb_exp_title_{i}")
                exp['company'] = st.text_input(f"Company##{i}", value=exp.get('company', ''), key=f"rb_exp_company_{i}")
                cols_date = st.columns(2)
                with cols_date[0]:
                    exp['start_date'] = st.text_input(f"Start Date (e.g., MM/YYYY)##{i}", value=exp.get('start_date', ''), key=f"rb_exp_start_{i}")
                with cols_date[1]:
                    exp['end_date'] = st.text_input(f"End Date (e.g., MM/YYYY or Present)##{i}", value=exp.get('end_date', ''), key=f"rb_exp_end_{i}")
                exp['description'] = st.text_area(f"Responsibilities/Achievements##{i}", value=exp.get('description', ''), height=150, key=f"rb_exp_desc_{i}",
                                                help="Use bullet points starting with '-' or '*' for best formatting. You can use action verbs from the suggestions below.")
                # Action verb suggestions could be a dropdown or just listed

        col_buttons = st.columns(2)
        with col_buttons[0]:
            if st.button("Add New Experience", key="add_exp_button"):
                st.session_state.rb_experience.append({'job_title': '', 'company': '', 'start_date': '', 'end_date': '', 'description': ''})
                st.rerun()
        with col_buttons[1]:
            if st.session_state.rb_experience and st.button("Remove Last Experience", type="secondary", key="remove_exp_button"):
                st.session_state.rb_experience.pop()
                st.rerun()

    elif current_step_index == 3: # Education
        st.markdown("<h4 class='custom-h4'>Education</h4>", unsafe_allow_html=True)
        for i, edu in enumerate(st.session_state.rb_education):
             with st.expander(f"Education {i+1}: {edu.get('degree', 'New Entry')}", expanded=True):
                edu['institution'] = st.text_input(f"Institution##{i}", value=edu.get('institution', ''), key=f"rb_edu_inst_{i}")
                edu['degree'] = st.text_input(f"Degree/Certificate##{i}", value=edu.get('degree', ''), key=f"rb_edu_degree_{i}")
                cols_edu_date = st.columns(2)
                with cols_edu_date[0]:
                    edu['grad_year'] = st.text_input(f"Graduation Year / Expected##{i}", value=edu.get('grad_year', ''), key=f"rb_edu_year_{i}")
                with cols_edu_date[1]:
                    edu['details'] = st.text_input(f"Details (e.g., GPA, Honors - Optional)##{i}", value=edu.get('details', ''), key=f"rb_edu_details_{i}")

        col_edu_buttons = st.columns(2)
        with col_edu_buttons[0]:
            if st.button("Add New Education", key="add_edu_button"):
                st.session_state.rb_education.append({'institution': '', 'degree': '', 'grad_year': '', 'details': ''})
                st.rerun()
        with col_edu_buttons[1]:
            if st.session_state.rb_education and st.button("Remove Last Education", type="secondary", key="remove_edu_button"):
                st.session_state.rb_education.pop()
                st.rerun()

    elif current_step_index == 4: # Skills
        st.markdown("<h4 class='custom-h4'>Skills</h4>", unsafe_allow_html=True)
        st.markdown(
            "<small>Enter skills separated by commas in the text box below. "
            "You can also select from the suggestions; use the 'Update Skills List from Suggestions' button to add them to your list. "
            "To remove skills, please edit the text box directly.</small>",
            unsafe_allow_html=True
        )
        add_vertical_space(1)

        # Convert list of skills to comma-separated string for text_area
        skills_str = ", ".join(st.session_state.rb_skills)
        updated_skills_str = st.text_area("Your Skills (comma-separated)", value=skills_str, key="rb_skills_text_area", height=100)

        current_skill_list_from_text_area = sorted(list(set([skill.strip() for skill in updated_skills_str.split(',') if skill.strip()])))

        # Only update and rerun if the list actually changed to prevent excessive reruns on typing
        if current_skill_list_from_text_area != sorted(list(set(st.session_state.rb_skills))):
             st.session_state.rb_skills = current_skill_list_from_text_area
             # No rerun here, text area naturally updates session state on next interaction elsewhere or button press

        if common_skills_options:
            st.markdown("<strong>Skill Suggestions (select to add):</strong>", unsafe_allow_html=True)
            # Store selections from multiselects temporarily before adding them
            skills_to_add_from_suggestions = set()

            for category, skills_list in common_skills_options.items():
                with st.expander(category):
                    # The default for multiselect should reflect what's ALREADY in rb_skills *that belongs to this category*
                    default_selection = [s for s in skills_list if s in st.session_state.rb_skills]
                    selected_cat_skills = st.multiselect(
                        f"Select {category.lower()} skills",
                        options=skills_list,
                        default=default_selection,
                        key=f"rb_cat_skills_{category.replace(' ', '_')}"
                    )
                    for skill in selected_cat_skills:
                        skills_to_add_from_suggestions.add(skill)

            if st.button("Add Selected Suggestions to Skills List", key="update_skills_btn"):
                newly_added_count = 0
                for skill_to_add in skills_to_add_from_suggestions:
                    if skill_to_add not in st.session_state.rb_skills:
                        st.session_state.rb_skills.append(skill_to_add)
                        newly_added_count +=1

                # Sort and remove duplicates after adding
                st.session_state.rb_skills = sorted(list(set(st.session_state.rb_skills)))

                if newly_added_count > 0:
                    st.toast(f"{newly_added_count} skill(s) added to your list!", icon="✨")
                else:
                    st.toast("No new skills were added from suggestions.", icon="🤷")
                st.rerun() # Rerun to update the text_area with newly added/consolidated skills

    elif current_step_index == 5: # Projects
        st.markdown("<h4 class='custom-h4'>Projects</h4>", unsafe_allow_html=True)
        # Similar structure to Experience/Education
        for i, proj in enumerate(st.session_state.rb_projects):
            with st.expander(f"Project {i+1}: {proj.get('name', 'New Project')}", expanded=True):
                proj['name'] = st.text_input(f"Project Name##{i}", value=proj.get('name', ''), key=f"rb_proj_name_{i}")
                proj['technologies'] = st.text_input(f"Technologies Used (comma-separated)##{i}", value=proj.get('technologies', ''), key=f"rb_proj_tech_{i}")
                proj['link'] = st.text_input(f"Project Link (Optional)##{i}", value=proj.get('link', ''), key=f"rb_proj_link_{i}")
                proj['description'] = st.text_area(f"Description##{i}", value=proj.get('description', ''), height=100, key=f"rb_proj_desc_{i}")

        col_proj_buttons = st.columns(2)
        with col_proj_buttons[0]:
            if st.button("Add New Project", key="add_proj_button"):
                st.session_state.rb_projects.append({'name': '', 'technologies': '', 'link': '', 'description': ''})
                st.rerun()
        with col_proj_buttons[1]:
            if st.session_state.rb_projects and st.button("Remove Last Project", type="secondary", key="remove_proj_button"):
                st.session_state.rb_projects.pop()
                st.rerun()

    elif current_step_index == 6: # Awards/Recognition
        st.markdown("<h4 class='custom-h4'>Awards / Recognition</h4>", unsafe_allow_html=True)
        for i, award in enumerate(st.session_state.rb_awards):
            with st.expander(f"Award {i+1}: {award.get('name', 'New Award')}", expanded=True):
                award['name'] = st.text_input(f"Award Name##{i}", value=award.get('name', ''), key=f"rb_award_name_{i}")
                award['organization'] = st.text_input(f"Awarding Organization##{i}", value=award.get('organization', ''), key=f"rb_award_org_{i}")
                award['year'] = st.text_input(f"Year Received##{i}", value=award.get('year', ''), key=f"rb_award_year_{i}")
                award['description'] = st.text_area(f"Brief Description (Optional)##{i}", value=award.get('description', ''), height=75, key=f"rb_award_desc_{i}")

        col_award_buttons = st.columns(2)
        with col_award_buttons[0]:
            if st.button("Add New Award", key="add_award_button"):
                st.session_state.rb_awards.append({'name': '', 'organization': '', 'year': '', 'description': ''})
                st.rerun()
        with col_award_buttons[1]:
            if st.session_state.rb_awards and st.button("Remove Last Award", type="secondary", key="remove_award_button"):
                st.session_state.rb_awards.pop()
                st.rerun()

    elif current_step_index == 7: # Review & Download
        st.markdown("<h4 class='custom-h4'>Review & Download Your Resume</h4>", unsafe_allow_html=True)
        add_vertical_space(1)

        # --- Display Three.js decorative element ---
        if 'threejs_scene_html_content' not in st.session_state:
            try:
                with open("threejs_scene.html", "r") as f:
                    st.session_state.threejs_scene_html_content = f.read()
            except FileNotFoundError:
                st.session_state.threejs_scene_html_content = "<p style='color:orange;'>Three.js scene HTML file not found.</p>"

        review_cols_main = st.columns([2,1]) # Give more space to review, less to 3D
        with review_cols_main[0]:
            # Consolidate all resume data from session state
            resume_data_for_pdf = {
                key: st.session_state[key] for key in st.session_state if key.startswith('rb_')
            }

            st.markdown("<h5>Quick Review:</h5>", unsafe_allow_html=True)
            # Display a summary for review (optional, could be more detailed)
            # review_cols = st.columns(2) # Nested columns might be too much
            # with review_cols[0]:
            st.markdown(f"**Name:** {st.session_state.get('rb_name', 'N/A')}")
            st.markdown(f"**Email:** {st.session_state.get('rb_email', 'N/A')}")
            st.markdown(f"**Phone:** {st.session_state.get('rb_phone', 'N/A')}")
            # with review_cols[1]:
            st.markdown(f"**Experience Entries:** {len(st.session_state.get('rb_experience', []))}")
            st.markdown(f"**Education Entries:** {len(st.session_state.get('rb_education', []))}")
            st.markdown(f"**Skills:** {', '.join(st.session_state.get('rb_skills', ['N/A']))[:70]}...")

            add_vertical_space(2)

            # Template Selection
            template_options = list(pdf_templates.TEMPLATE_FUNCTIONS.keys())
            selected_template = st.selectbox("Choose a Resume Template:", template_options, key="rb_template_select")

            # PDF Generation and Download
            if st.button("Generate & Download PDF 📄", key="rb_generate_download_pdf", type="primary"):
                if selected_template and selected_template in pdf_templates.TEMPLATE_FUNCTIONS:
                    pdf_function = pdf_templates.TEMPLATE_FUNCTIONS[selected_template]
                    try:
                        with st.spinner(f"Generating PDF with '{selected_template}' template..."):
                            pdf_buffer = pdf_function(resume_data_for_pdf)

                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_buffer,
                            file_name=f"{st.session_state.get('rb_name', 'resume').replace(' ', '_')}_{selected_template.lower().replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key="rb_pdf_download_final"
                        )
                        st.success("PDF generated successfully! Click download if it didn't start automatically.")
                    except Exception as e:
                        st.error(f"Error generating PDF: {e}")
                        print(f"PDF Generation Error: {e}")
                else:
                    st.warning("Please select a valid template.")

        with review_cols_main[1]:
            if st.session_state.threejs_scene_html_content and not st.session_state.threejs_scene_html_content.startswith("<p style='color:orange;'>"):
                 st.components.v1.html(st.session_state.threejs_scene_html_content, height=300, width=250) # Adjust size as needed
            else:
                 st.markdown(st.session_state.threejs_scene_html_content, unsafe_allow_html=True) # Show error if file not found

        add_vertical_space(1)
        st.markdown("<h6>Full Data (for debugging):</h6>", unsafe_allow_html=True)
        review_cols = st.columns(2)
        with review_cols[0]:
            st.markdown(f"**Name:** {st.session_state.get('rb_name', 'N/A')}")
            st.markdown(f"**Email:** {st.session_state.get('rb_email', 'N/A')}")
            st.markdown(f"**Phone:** {st.session_state.get('rb_phone', 'N/A')}")
        with review_cols[1]:
            st.markdown(f"**Experience Entries:** {len(st.session_state.get('rb_experience', []))}")
            st.markdown(f"**Education Entries:** {len(st.session_state.get('rb_education', []))}")
            st.markdown(f"**Skills:** {', '.join(st.session_state.get('rb_skills', ['N/A']))[:70]}...")

        add_vertical_space(2)

        # Template Selection
        template_options = list(pdf_templates.TEMPLATE_FUNCTIONS.keys())
        selected_template = st.selectbox("Choose a Resume Template:", template_options, key="rb_template_select")

        # PDF Generation and Download
        if st.button("Generate & Download PDF 📄", key="rb_generate_download_pdf", type="primary"):
            if selected_template and selected_template in pdf_templates.TEMPLATE_FUNCTIONS:
                pdf_function = pdf_templates.TEMPLATE_FUNCTIONS[selected_template]
                try:
                    with st.spinner(f"Generating PDF with '{selected_template}' template..."):
                        pdf_buffer = pdf_function(resume_data_for_pdf)

                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_buffer,
                        file_name=f"{st.session_state.get('rb_name', 'resume').replace(' ', '_')}_{selected_template.lower().replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key="rb_pdf_download_final"
                    )
                    st.success("PDF generated successfully! Click download if it didn't start automatically.")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")
                    # You might want to log the full traceback here for debugging
                    print(f"PDF Generation Error: {e}") # For server-side logs
            else:
                st.warning("Please select a valid template.")

        add_vertical_space(1)
        st.markdown("<h6>Full Data (for debugging):</h6>", unsafe_allow_html=True)
        with st.expander("Show all resume data (JSON)", expanded=False):
            st.json(resume_data_for_pdf)


    else:
        st.markdown(f"<h4 class='custom-h4'>{steps_items[current_step_index].title}</h4>", unsafe_allow_html=True)
        st.write(f"Content for {steps_items[current_step_index].title} coming soon.")

    # --- Navigation Buttons ---
    add_vertical_space(2)
    nav_cols = st.columns([1, 1, 1]) # Ratio for button placement
    with nav_cols[0]:
        if current_step_index > 0:
            if st.button("⬅️ Previous", key="rb_prev_step"):
                st.session_state.rb_step_index = max(0, current_step_index - 1)
                st.rerun()
    with nav_cols[2]:
        if current_step_index < len(steps_items) - 1:
            if st.button("Next ➡️", key="rb_next_step"):
                st.session_state.rb_step_index = min(len(steps_items) - 1, current_step_index + 1)
                st.rerun()
        # The "Download PDF" button is now part of the step 7 content itself.
        # else: # On Review & Download step (last step)
            # The generate/download button is now inside the step's content area
            # No primary "Next" button needed here.
            pass


elif page == "Account" or page == "Preferences": # Handle Settings sub-menu clicks
    st.header(page)
    add_vertical_space(2)
    sac.alert(label='Under Construction', description=f'The {page} settings are not yet available.',
              type='warning', icon=True, banner=True)
    add_vertical_space(2)
    st.markdown(f"<p style='text-align: center; color: #cccccc;'>Customize your experience and manage your account details here in the future.</p>", unsafe_allow_html=True)
