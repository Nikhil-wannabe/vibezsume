import streamlit as st
# Removed: import streamlit_antd_components as sac -> Not used directly in app.py anymore
from streamlit_lottie import st_lottie
from streamlit_extras.add_vertical_space import add_vertical_space
# Removed unused standard library imports: os, time, json, io

# --- Global App Configuration ---
st.set_page_config(
    layout="wide",
    page_title="AI Resume Toolkit - Home",
    initial_sidebar_state="expanded",
    page_icon="🏠"
)

# --- Global Scripts & Styles ---
# GSAP Library (Load Once Globally)
st.markdown("""
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
""", unsafe_allow_html=True)

# Custom CSS (Global)
CUSTOM_CSS = """
<style>
    /* Base theme and layout */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #e0e0e0;
        background-color: #1a1a1a;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }

    /* Sidebar styling */
    .stSidebar {
        background-color: #262626;
        padding: 1rem;
    }
    .stSidebar .sidebar-content {
        padding-top: 0.5rem;
    }

    /* Styling for Streamlit's auto-generated page navigation in sidebar */
    /* Targeting general sidebar nav links for now. These selectors are based on common Streamlit HTML structure
       and might need updates if Streamlit changes its internal HTML significantly. */
    ul[data-testid="st- αυτόματη πλοήγηση"] > li > a,
    ul[data-testid="st- αυτόματη πλοήγηση"] > li > div[data-testid="stExpandable"] > div[role="button"]
    {
        padding: 0.6rem 0.75rem !important;
        border-radius: 0.375rem !important;
        margin-bottom: 0.2rem;
    }
    ul[data-testid="st- αυτόματη πλοήγηση"] > li > a:hover,
    ul[data-testid="st- αυτόματη πλοήγηση"] > li > div[data-testid="stExpandable"] > div[role="button"]:hover {
        background-color: #333333 !important;
        color: #ffffff !important;
    }
    /* Active/selected page link */
    ul[data-testid="st- αυτόματη πλοήγηση"] > li > a[aria-current="page"],
    ul[data-testid="st- αυτόματη πλοήγηση"] > li > div[data-testid="stExpandable"][aria-expanded="true"] > div[role="button"] {
        background-color: #4CAF50 !important;
        color: #ffffff !important;
    }
    /* Icons within navigation links */
    ul[data-testid="st- αυτόματη πλοήγηση"] > li > a .st-emotion-cache-1fv6orm,
    ul[data-testid="st- αυτόματη πλοήγηση"] > li > div[data-testid="stExpandable"] > div[role="button"] .st-emotion-cache-1fv6orm
    {
         color: inherit !important;
         font-size: 1.0em;
         margin-right: 0.6rem;
    }

    /* General UI elements styling */
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
    .stButton>button[kind="secondary"] {
        border-color: #555;
        color: #ccc;
    }
    .stButton>button[kind="secondary"]:hover {
        background-color: #444;
        border-color: #666;
        color: white;
    }

    .stFileUploader label { color: #e0e0e0 !important; }
    .stFileUploader > div > button {
        border: 1px solid #4CAF50;
        background-color: #2a2a2a;
        color: #e0e0e0;
        border-radius: 5px;
    }
    .stFileUploader > div > button:hover {
        background-color: #3a3a3a;
        border-color: #5cb85c;
    }
    .stTextInput > div > div > input, .stTextArea > div > textarea {
        background-color: #2a2a2a;
        color: #e0e0e0;
        border: 1px solid #444;
        border-radius: 5px;
    }
    .stTextInput > label, .stTextArea > label { color: #e0e0e0 !important; }

    /* Text and Card styling */
    p, .stMarkdown, .stWrite { color: #cccccc; }
    .stAlert { margin-top: 1rem; margin-bottom: 1rem; }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeIn 0.5s ease-out forwards; }

    .info-card {
        background-color: #2a2a2a;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #3a3a3a;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .info-card h4 { margin-bottom: 10px; color: #4CAF50; }
    .info-card p { margin-bottom: 5px; color: #e0e0e0; }
    .info-card .icon { margin-right: 8px; color: #4CAF50; }

    .custom-h4 {
        color: #4CAF50;
        font-size: 1.25em;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def initialize_global_session_state():
    """
    Initializes session state variables that are shared or accessed across multiple pages.
    This function is called once when the app starts.
    """
    # Stores results from Resume Analyzer, used by Job Analyzer
    if 'resume_analysis_results' not in st.session_state:
        st.session_state.resume_analysis_results = None

    # Stores job description text (from URL or paste) in Job Analyzer
    if 'job_description_text' not in st.session_state:
        st.session_state.job_description_text = ""

    # Stores analysis results of the job description in Job Analyzer
    if 'job_analysis_results' not in st.session_state:
        st.session_state.job_analysis_results = None

initialize_global_session_state()


def _display_sidebar_content():
    """Renders the global sidebar content."""
    LOTTIE_SIDEBAR_URL = "https://assetslottiefiles.com/packages/lf20_CgY9IR7yC9.json"
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; color: #4CAF50; font-size: 1.8em;'>AI Resume Toolkit</h1>", unsafe_allow_html=True)
        try:
            st_lottie(LOTTIE_SIDEBAR_URL, speed=1, reverse=False, loop=True, quality="low",
                      height=120, width="90%", key="sidebar_lottie_global")
        except Exception as e:
            st.error(f"Lottie Error (Sidebar): {e}") # Display error in sidebar if Lottie fails
        add_vertical_space(1)

        st.markdown("---")
        st.caption("Navigate using the links above.")
        add_vertical_space(2)
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; font-size: 0.85em; color: #cccccc;'>"
            "Developed by the <br>AI Resume Toolkit Team"
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div style='text-align: center; font-size: 0.75em; color: #888888; padding-top: 0.5em;'>"
            "Powered by Streamlit"
            "</div>",
            unsafe_allow_html=True
        )

_display_sidebar_content()


def render_home_page_content():
    """Renders the content for the main home page (app.py)."""
    st.title("Welcome to the AI Resume Toolkit! 🚀")
    st.markdown(
        """
        Unlock your career potential! This toolkit offers a suite of AI-powered tools to help you
        analyze, build, and optimize your resume and job applications.
        Select a tool from the sidebar to get started.
        """
    )
    add_vertical_space(2)

    st.subheader("Explore Our Tools:")
    cols = st.columns(3)
    card_style = "text-align:center; height: 180px; display: flex; flex-direction: column; justify-content: center; align-items: center;"

    with cols[0]:
        st.markdown(
            f"""
            <div class="info-card" style="{card_style}">
                <h4>📝<br>Resume Analyzer</h4>
                <p style="font-size:0.9em;">Upload your resume to extract key information, understand its structure, and prepare for detailed analysis.</p>
            </div>
            """, unsafe_allow_html=True
        )
    with cols[1]:
        st.markdown(
            f"""
            <div class="info-card" style="{card_style}">
                <h4>🔍<br>Job Analyzer</h4>
                <p style="font-size:0.9em;">Analyze job descriptions from URLs or pasted text. Compare requirements against your analyzed resume to identify skill gaps and matches.</p>
            </div>
            """, unsafe_allow_html=True
        )
    with cols[2]:
        st.markdown(
            f"""
            <div class="info-card" style="{card_style}">
                <h4>🛠️<br>Resume Builder</h4>
                <p style="font-size:0.9em;">Craft a new, professional resume from scratch or refine existing content using our guided step-by-step builder.</p>
            </div>
            """, unsafe_allow_html=True
        )

    add_vertical_space(2)
    st.markdown("---")
    st.markdown(
        """
        **How to Get Started:**
        1.  Navigate to the **📝 Resume Analyzer** to upload and process your current resume. This is a good first step as the extracted data can be used by other tools.
        2.  Use the **🔍 Job Analyzer** to input a job description. If you've analyzed your resume, you'll see a direct comparison.
        3.  Explore the **🛠️ Resume Builder** to create a new resume or structure your existing information professionally.

        The **⚙️ Settings** page is a placeholder for future application configurations.
        """
    )
    add_vertical_space(2)
    st.info("This application is a demonstration project. Always review generated content carefully before use.", icon="💡")

if __name__ == "__main__":
    # This ensures that the home page content is rendered when app.py is run directly.
    # Streamlit's multi-page app feature handles rendering of pages in the `pages/` directory.
    render_home_page_content()
