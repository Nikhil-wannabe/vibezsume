import streamlit as st
import streamlit_antd_components as sac # For sac.steps and other UI elements
from streamlit_extras.add_vertical_space import add_vertical_space
import json # For loading predefined_options.json
import io   # For PDF in-memory buffer
from typing import Dict, List, Any, Callable # For type hinting

# Assuming utils are in a directory accessible from pages, or PYTHONPATH is set
from utils import pdf_templates

# --- Constants & Configurations ---
RB_FIELDS_DEFINITIONS: Dict[str, Any] = {
    'rb_name': '', 'rb_email': '', 'rb_phone': '', 'rb_linkedin': '', 'rb_portfolio': '',
    'rb_summary': '',
    'rb_experience': [],
    'rb_education': [],
    'rb_skills': [],
    'rb_projects': [],
    'rb_awards': []
}
PREDEFINED_OPTIONS_PATH: str = "data/predefined_options.json"

# --- Page-Specific Session State Initialization ---
def _initialize_rb_state():
    """Initializes session state variables for the Resume Builder if they don't exist."""
    for field, default_value in RB_FIELDS_DEFINITIONS.items():
        if field not in st.session_state:
            # Ensure mutable defaults like lists are copied to avoid shared state issues
            st.session_state[field] = list(default_value) if isinstance(default_value, list) else default_value
    if 'rb_step_index' not in st.session_state:
        st.session_state.rb_step_index = 0
    if 'threejs_scene_html_content' not in st.session_state:
        st.session_state.threejs_scene_html_content = None # Will be loaded on demand

def _reset_rb_state():
    """Resets all Resume Builder form data to their default initial states."""
    for field, default_value in RB_FIELDS_DEFINITIONS.items():
        st.session_state[field] = list(default_value) if isinstance(default_value, list) else default_value
    st.session_state.rb_step_index = 0
    st.toast("Resume Builder data cleared and reset!", icon="🗑️")

# --- Data Loading ---
@st.cache_data # Cache to avoid reloading file on every rerun
def _load_predefined_options() -> Dict[str, Any]:
    """Loads skill suggestions and action verbs from the JSON file."""
    try:
        with open(PREDEFINED_OPTIONS_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Critical Error: `{PREDEFINED_OPTIONS_PATH}` not found. Options will be unavailable.")
        return {"common_skills": {}, "action_verbs": []}
    except json.JSONDecodeError:
        st.error(f"Error: Could not parse `{PREDEFINED_OPTIONS_PATH}`. Ensure it's valid JSON.")
        return {"common_skills": {}, "action_verbs": []}

# --- UI Helper Functions for Form Sections ---
def _display_personal_info_form():
    """Renders the form fields for personal information."""
    st.markdown("<h4 class='custom-h4'>Personal Information</h4>", unsafe_allow_html=True)
    st.session_state.rb_name = st.text_input("Full Name", value=st.session_state.rb_name, key="rb_form_widget_name")
    c1, c2 = st.columns(2)
    st.session_state.rb_email = c1.text_input("Email Address", value=st.session_state.rb_email, key="rb_form_widget_email")
    st.session_state.rb_phone = c2.text_input("Phone Number", value=st.session_state.rb_phone, key="rb_form_widget_phone")
    st.session_state.rb_linkedin = c1.text_input("LinkedIn Profile URL (Optional)", value=st.session_state.rb_linkedin, key="rb_form_widget_linkedin")
    st.session_state.rb_portfolio = c2.text_input("Portfolio/Website URL (Optional)", value=st.session_state.rb_portfolio, key="rb_form_widget_portfolio")

def _display_summary_form():
    """Renders the form field for the resume summary/objective."""
    st.markdown("<h4 class='custom-h4'>Summary / Objective</h4>", unsafe_allow_html=True)
    st.session_state.rb_summary = st.text_area(
        "Write a brief summary or objective (2-4 sentences)", value=st.session_state.rb_summary,
        height=150, key="rb_form_widget_summary", help="Highlight your key qualifications and career goals."
    )
    word_count = len(st.session_state.rb_summary.split()) if st.session_state.rb_summary.strip() else 0
    st.caption(f"Word count: {word_count}") # Using st.caption for less intrusive text

def _display_dynamic_list_form(section_title: str, session_key: str, item_fields: Dict[str, Dict[str, Any]], add_label: str, item_singular_name: str):
    """Generic function to display and manage a list of entries (e.g., experience, education)."""
    st.markdown(f"<h4 class='custom-h4'>{section_title}</h4>", unsafe_allow_html=True)

    # Iterate over a copy of the list's indices to allow safe removal
    for i in range(len(st.session_state[session_key])):
        item_data = st.session_state[session_key][i] # Get current item data
        with st.container():
            header_preview = str(item_data.get(list(item_fields.keys())[0], "")[:25])
            st.markdown(f"<div class='info-card' style='padding-top:0.5rem; margin-bottom:1rem;'>", unsafe_allow_html=True)
            st.markdown(f"<h6>{item_singular_name} {i+1} {' (' + header_preview + '...)' if header_preview else ''}</h6>", unsafe_allow_html=True)

            for field_key, config in item_fields.items():
                widget_type = config.get("type", "text_input")
                label = config.get("label", field_key.replace('_', ' ').capitalize())
                default_val = item_data.get(field_key, '') # Get current value for this item

                if widget_type == "text_area":
                    item_data[field_key] = st.text_area(label, value=default_val, height=config.get("height", 100), key=f"{session_key}_{i}_{field_key}_widget")
                else:
                    item_data[field_key] = st.text_input(label, value=default_val, key=f"{session_key}_{i}_{field_key}_widget")

            if st.button(f"🗑️ Remove {item_singular_name} {i+1}", key=f"remove_{session_key}_{i}_btn_widget", type="secondary"):
                st.session_state[session_key].pop(i)
                st.rerun() # Rerun to reflect removal
            st.markdown("</div>", unsafe_allow_html=True)

    if st.button(f"➕ {add_label}", key=f"add_{session_key}_main_btn_widget"):
        st.session_state[session_key].append({field_key: '' for field_key in item_fields})
        st.rerun() # Rerun to show new entry form

def _display_skills_form(common_skills_data: Dict[str, List[str]]):
    """Renders the form for skills input and suggestions."""
    st.markdown("<h4 class='custom-h4'>Skills</h4>", unsafe_allow_html=True)
    st.caption( # Using st.caption for help text
        "Enter skills separated by commas. Use suggestions to add common skills, "
        "then refine your list in the text box. To remove skills, edit the text box directly."
    )
    add_vertical_space(1)

    skills_as_string = ", ".join(st.session_state.rb_skills)
    updated_skills_string = st.text_area("Your Skills (comma-separated)", value=skills_as_string,
                                         key="rb_form_widget_skills_text_area", height=100,
                                         help="Edit this list directly or use suggestions below.")
    # Update session state from text area; this happens on each interaction due to Streamlit's model
    st.session_state.rb_skills = sorted(list(set([s.strip() for s in updated_skills_string.split(',') if s.strip()])))

    if common_skills_data:
        st.markdown("<strong>Skill Suggestions:</strong>", unsafe_allow_html=True)
        skills_to_add_from_multiselects = set()

        for category, skill_list_for_category in common_skills_data.items():
            with st.expander(f"{category} Skills"):
                defaults_for_multiselect = [s for s in skill_list_for_category if s in st.session_state.rb_skills]
                selected_skills = st.multiselect(
                    f"Select {category.lower()} skills to add", options=skill_list_for_category,
                    default=defaults_for_multiselect,
                    key=f"rb_form_widget_skills_multiselect_{category.replace(' ', '_')}"
                )
                for skill in selected_skills: skills_to_add_via_multiselect.add(skill)

        if st.button("Add Selected Suggestions to Skills List", key="rb_form_widget_skills_add_suggestions_btn"):
            original_skill_count = len(st.session_state.rb_skills)
            st.session_state.rb_skills.extend(list(skills_to_add_via_multiselect))
            st.session_state.rb_skills = sorted(list(set(st.session_state.rb_skills))) # De-duplicate and sort
            newly_added_count = len(st.session_state.rb_skills) - original_skill_count

            if newly_added_count > 0: st.toast(f"{newly_added_count} unique skill(s) confirmed in your list!", icon="✨")
            else: st.toast("No new skills were added from suggestions, or they were already in your list.", icon="🤷")
            st.rerun()

def _display_review_and_download_section(action_verbs_list: List[str]): # Added action_verbs_list
    """Renders the review, template selection, and PDF download section."""
    st.markdown("<h4 class='custom-h4'>Review & Download Your Resume</h4>", unsafe_allow_html=True)
    add_vertical_space(1)

    if st.session_state.get('threejs_scene_html_content') is None:
        try:
            with open("threejs_scene.html", "r") as f: st.session_state.threejs_scene_html_content = f.read()
        except FileNotFoundError:
            st.session_state.threejs_scene_html_content = "<p style='color:orange;'><i>Three.js scene HTML file not found.</i></p>"

    col_review_main, col_threejs = st.columns([2,1])
    with col_review_main:
        resume_data_for_pdf = {key: st.session_state[key] for key in st.session_state if key.startswith('rb_')}

        st.markdown("<h6>Quick Review:</h6>", unsafe_allow_html=True) # Changed to H6 for smaller review title
        st.markdown(f"**Name:** {resume_data_for_pdf.get('rb_name', '(Not set)')}")
        st.markdown(f"**Email:** {resume_data_for_pdf.get('rb_email', '(Not set)')}")
        st.markdown(f"**Experience Entries:** {len(resume_data_for_pdf.get('rb_experience', []))}")
        skills_preview = resume_data_for_pdf.get('rb_skills', [])
        st.markdown(f"**Skills:** {', '.join(skills_preview if skills_preview else ['(None)'])[:70]}...")
        add_vertical_space(1) # Reduced space

        template_options = list(pdf_templates.TEMPLATE_FUNCTIONS.keys())
        selected_template = st.selectbox("Choose Resume Template:", template_options, key="rb_form_widget_template_select")

        if st.button("Generate & Download PDF 📄", key="rb_form_widget_generate_pdf_btn", type="primary"):
            if selected_template and selected_template in pdf_templates.TEMPLATE_FUNCTIONS:
                pdf_generation_func = pdf_templates.TEMPLATE_FUNCTIONS[selected_template]
                try:
                    with st.spinner(f"Generating PDF using '{selected_template}' template..."):
                        pdf_bytes_io = pdf_generation_func(resume_data_for_pdf) # Pass data

                    file_name_prefix = resume_data_for_pdf.get('rb_name', 'resume').replace(' ', '_') or "resume"
                    download_file_name = f"{file_name_prefix}_{selected_template.lower().replace(' ', '_')}.pdf"

                    st.download_button(
                        label="📥 Download PDF", data=pdf_bytes_io,
                        file_name=download_file_name, mime="application/pdf",
                        key="rb_form_widget_download_pdf_btn"
                    )
                    st.success("PDF ready! Click 'Download PDF'.")
                except Exception as e:
                    st.error(f"Error during PDF generation: {e}")
                    print(f"PDF Generation Error (Resume Builder): {e}")
            else:
                st.warning("Please select a valid PDF template.")

    with col_threejs:
        if st.session_state.threejs_scene_html_content and \
           not st.session_state.threejs_scene_html_content.startswith("<p style='color:orange;'>"):
             st.components.v1.html(st.session_state.threejs_scene_html_content, height=250, width=250)
        else:
             st.markdown(st.session_state.threejs_scene_html_content, unsafe_allow_html=True)

    with st.expander("Show all entered resume data (JSON for debugging)", expanded=False):
        st.json({k: v for k, v in st.session_state.items() if k.startswith('rb_')})

def _display_navigation_buttons(current_step_idx: int, total_steps: int):
    """Displays Previous/Next navigation buttons for the steps."""
    add_vertical_space(1) # Reduced space
    nav_cols = st.columns([1, 1, 1])
    if current_step_idx > 0:
        if nav_cols[0].button("⬅️ Previous Step", key="rb_form_widget_prev_step_btn"):
            st.session_state.rb_step_index = max(0, current_step_idx - 1)
            st.rerun()
    if current_step_idx < total_steps - 1:
        if nav_cols[2].button("Next Step ➡️", key="rb_form_widget_next_step_btn"):
            st.session_state.rb_step_index = min(total_steps - 1, current_step_idx + 1)
            st.rerun()

# --- Main Page Rendering Function ---
def render_resume_builder_page():
    """Main function to orchestrate the rendering of the Resume Builder page."""
    _initialize_rb_state()

    predefined_data = _load_predefined_options()
    common_skills_data = predefined_data.get("common_skills", {})
    action_verbs_list = predefined_data.get("action_verbs", [])

    st.title("🛠️ Resume Builder")
    st.markdown("<p style='color: #cccccc;'>Craft your professional resume step-by-step using the form below.</p>", unsafe_allow_html=True)
    add_vertical_space(1)

    if st.button("🗑️ Start Over / Clear All Data", key="rb_clear_all_data_btn_mainwidget", type="secondary",
                  help="Clears all fields in the Resume Builder and resets to the first step."):
        _reset_rb_state()
        st.rerun()

    steps_definition = [
        sac.StepsItem(title='Personal', description='Contact Details', icon='person-badge'),
        sac.StepsItem(title='Summary', description='Objective/Profile', icon='text-paragraph'),
        sac.StepsItem(title='Experience', description='Work History', icon='briefcase'),
        sac.StepsItem(title='Education', description='Qualifications', icon='book'),
        sac.StepsItem(title='Skills', description='Your Abilities', icon='tools'),
        sac.StepsItem(title='Projects', description='Showcase Your Work', icon='kanban'),
        sac.StepsItem(title='Awards', description='Recognitions', icon='award'),
        sac.StepsItem(title='Review', description='Preview & Download', icon='file-earmark-arrow-down') # Changed icon
    ]
    current_step_idx = st.session_state.get('rb_step_index', 0)

    sac.steps(items=steps_definition, index=current_step_idx, format_func='title',
              placement='horizontal', variant='navigation', readonly=True,
              key="rb_steps_nav_display_widget") # Changed key
    add_vertical_space(1) # Reduced space

    # Define field configurations for dynamic list forms
    experience_fields = {
        'job_title': {"label": "Job Title"}, 'company': {"label": "Company"},
        'start_date': {"label": "Start Date (e.g., MM/YYYY)"}, 'end_date': {"label": "End Date (e.g., MM/YYYY or Present)"},
        'description': {"label": "Responsibilities/Achievements (use '-' or '*' for bullets)", "type": "text_area", "height": 150}
    }
    education_fields = {
        'institution': {"label": "Institution"}, 'degree': {"label": "Degree/Certificate"},
        'grad_year': {"label": "Graduation Year / Expected"}, 'details': {"label": "Details (e.g., GPA, Honors - Optional)"}
    }
    project_fields = {
        'name': {"label": "Project Name"}, 'technologies': {"label": "Technologies Used (comma-separated)"},
        'link': {"label": "Project Link (Optional)"},
        'description': {"label": "Description (use '-' or '*' for bullets)", "type": "text_area", "height": 100}
    }
    award_fields = {
        'name': {"label": "Award Name"}, 'organization': {"label": "Awarding Organization"},
        'year': {"label": "Year Received"},
        'description': {"label": "Brief Description (Optional)", "type": "text_area", "height": 75}
    }

    # Dispatch to the appropriate form display function based on current step
    if current_step_idx == 0: _display_personal_info_form()
    elif current_step_idx == 1: _display_summary_form()
    elif current_step_idx == 2: _display_dynamic_list_form("Work Experience", "rb_experience", experience_fields, "Add New Experience", "Experience")
    elif current_step_idx == 3: _display_dynamic_list_form("Education", "rb_education", education_fields, "Add New Education", "Education")
    elif current_step_idx == 4: _display_skills_form(common_skills_data)
    elif current_step_idx == 5: _display_dynamic_list_form("Projects", "rb_projects", project_fields, "Add New Project", "Project")
    elif current_step_idx == 6: _display_dynamic_list_form("Awards / Recognition", "rb_awards", award_fields, "Add New Award", "Award")
    elif current_step_idx == 7: _display_review_and_download_section(action_verbs) # Pass action_verbs if needed by review/PDF
    else: st.error("Invalid step. Please use navigation buttons or restart the builder.")

    _display_navigation_buttons(current_step_idx, len(steps_definition))

# --- Main execution call for the page ---
render_resume_builder_page()
