import streamlit as st
import streamlit_antd_components as sac # Import Antd Components
from streamlit_lottie import st_lottie # Import Lottie for animations
from streamlit_extras.add_vertical_space import add_vertical_space # For spacing
from utils.resume_parser import extract_text_from_pdf, extract_text_from_docx, parse_resume_text
import os
import time # To simulate processing time

# Set page config - Using "wide" layout and a dark theme by default from Streamlit's options
st.set_page_config(layout="wide", page_title="AI Resume Toolkit", initial_sidebar_state="expanded")

# Custom CSS for modern look and feel
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
            st.markdown("<div class='fade-in'>", unsafe_allow_html=True)

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

            # Placeholder for other sections (can also be styled as cards or alerts)
            st.markdown("---") # Visual separator
            st.markdown("<h4 class='custom-h4'><span class='icon'>👔</span>Experience</h4>", unsafe_allow_html=True)
            st.markdown("<p><em>(Placeholder - Not yet implemented)</em></p>", unsafe_allow_html=True)

            st.markdown("<h4 class='custom-h4'><span class='icon'>🎓</span>Education</h4>", unsafe_allow_html=True)
            st.markdown("<p><em>(Placeholder - Not yet implemented)</em></p>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True) # End of fade-in div

        else:
            st.error("Could not extract text from the uploaded file.")

elif page == "Job Analyzer":
    st.header("Job Analyzer")
    add_vertical_space(2)
    sac.alert(label='Coming Soon!', description='This feature is currently under development. Stay tuned for updates!',
              type='info', icon=True, banner=True)
    add_vertical_space(2)
    st.markdown("<p style='text-align: center; color: #cccccc;'>The Job Analyzer will help you match your resume to job descriptions and identify key areas for improvement.</p>", unsafe_allow_html=True)
    # You could add a Lottie animation here too, e.g., a "construction" or "search" animation
    # st_lottie("URL_TO_CONSTRUCTION_LOTTIE", height=200)

elif page == "Resume Builder":
    st.header("Resume Builder")
    add_vertical_space(2)
    sac.alert(label='Coming Soon!', description='Create a professional resume from scratch using our guided builder. Coming soon!',
              type='info', icon=True, banner=True)
    add_vertical_space(2)
    st.markdown("<p style='text-align: center; color: #cccccc;'>Our Resume Builder will offer various templates and AI suggestions to craft the perfect resume.</p>", unsafe_allow_html=True)

elif page == "Account" or page == "Preferences": # Handle Settings sub-menu clicks
    st.header(page)
    add_vertical_space(2)
    sac.alert(label='Under Construction', description=f'The {page} settings are not yet available.',
              type='warning', icon=True, banner=True)
    add_vertical_space(2)
    st.markdown(f"<p style='text-align: center; color: #cccccc;'>Customize your experience and manage your account details here in the future.</p>", unsafe_allow_html=True)
