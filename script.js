document.addEventListener("DOMContentLoaded", function() {
    // DOM Elements
    const homeSection = document.getElementById("home-section");
    const builderSection = document.getElementById("builder-section");
    const previewSection = document.getElementById("preview-section");
    
    const homeLink = document.getElementById("home-link");
    const builderLink = document.getElementById("builder-link");
    const startBuilderBtn = document.getElementById("start-builder");
    
    const resumeForm = document.getElementById("resume-form");
    const formSteps = document.querySelectorAll(".form-step");
    const progressSteps = document.querySelectorAll(".progress-bar .step");
    
    const nextBtns = document.querySelectorAll(".next-btn");
    const prevBtns = document.querySelectorAll(".prev-btn");
    
    const skillInput = document.getElementById("skill-input");
    const addSkillBtn = document.getElementById("add-skill-btn");
    const skillsList = document.getElementById("skills-list");
    const skillsInput = document.getElementById("skills");
    
    const editResumeBtn = document.getElementById("edit-resume-btn");
    const downloadResumeBtn = document.getElementById("download-resume-btn");
    const resumePreview = document.getElementById("resume-preview");
    
    // Current step tracker
    let currentStep = 1;
    
    // Store skills array
    let skills = [];
    
    // Navigation between sections
    homeLink.addEventListener("click", function(e) {
        e.preventDefault();
        showHomeSection();
    });
    
    builderLink.addEventListener("click", function(e) {
        e.preventDefault();
        showBuilderSection();
    });
    
    startBuilderBtn.addEventListener("click", function() {
        showBuilderSection();
    });
    
    function showHomeSection() {
        homeSection.classList.remove("hidden");
        builderSection.classList.add("hidden");
        previewSection.classList.add("hidden");
        
        homeLink.classList.add("active");
        builderLink.classList.remove("active");
    }
    
    function showBuilderSection() {
        homeSection.classList.add("hidden");
        builderSection.classList.remove("hidden");
        previewSection.classList.add("hidden");
        
        homeLink.classList.remove("active");
        builderLink.classList.add("active");
    }
    
    function showPreviewSection() {
        homeSection.classList.add("hidden");
        builderSection.classList.add("hidden");
        previewSection.classList.remove("hidden");
        
        homeLink.classList.remove("active");
        builderLink.classList.add("active");
    }
    
    // Form step navigation
    nextBtns.forEach(button => {
        button.addEventListener("click", function() {
            // Simple validation for required fields in step 1
            if (currentStep === 1) {
                const nameInput = document.getElementById("name");
                const emailInput = document.getElementById("email");
                const phoneInput = document.getElementById("phone");
                
                if (!nameInput.value || !emailInput.value || !phoneInput.value) {
                    alert("Please fill in all required fields.");
                    return;
                }
            }
            
            // Hide current step
            formSteps[currentStep - 1].classList.add("hidden");
            
            // Update current step
            currentStep++;
            
            // Show next step
            formSteps[currentStep - 1].classList.remove("hidden");
            
            // Update progress bar
            updateProgressBar();
        });
    });
    
    prevBtns.forEach(button => {
        button.addEventListener("click", function() {
            // Hide current step
            formSteps[currentStep - 1].classList.add("hidden");
            
            // Update current step
            currentStep--;
            
            // Show previous step
            formSteps[currentStep - 1].classList.remove("hidden");
            
            // Update progress bar
            updateProgressBar();
        });
    });
    
    function updateProgressBar() {
        progressSteps.forEach((step, index) => {
            if (index + 1 <= currentStep) {
                step.classList.add("active");
            } else {
                step.classList.remove("active");
            }
        });
    }
    
    // Skills management
    addSkillBtn.addEventListener("click", addSkill);
    
    skillInput.addEventListener("keypress", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            addSkill();
        }
    });
    
    function addSkill() {
        const skill = skillInput.value.trim();
        
        if (skill && !skills.includes(skill)) {
            // Add to skills array
            skills.push(skill);
            
            // Create skill tag
            const skillTag = document.createElement("div");
            skillTag.className = "skill-tag";
            
            skillTag.innerHTML = `
                <span>${skill}</span>
                <button type="button" class="remove-skill" data-skill="${skill}">×</button>
            `;
            
            skillsList.appendChild(skillTag);
            
            // Update hidden input
            skillsInput.value = JSON.stringify(skills);
            
            // Clear input
            skillInput.value = "";
        }
        
        skillInput.focus();
    }
    
    // Remove skill
    skillsList.addEventListener("click", function(e) {
        if (e.target.classList.contains("remove-skill")) {
            const skillToRemove = e.target.getAttribute("data-skill");
            
            // Remove from array
            skills = skills.filter(skill => skill !== skillToRemove);
            
            // Remove from DOM
            e.target.parentElement.remove();
            
            // Update hidden input
            skillsInput.value = JSON.stringify(skills);
        }
    });
    
    // Form submission
    resumeForm.addEventListener("submit", function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(resumeForm);
        const resumeData = {
            name: formData.get("name"),
            email: formData.get("email"),
            phone: formData.get("phone"),
            experience: formData.get("experience"),
            education: formData.get("education"),
            skills: skills,
            summary: formData.get("summary")
        };
        
        // Generate resume preview
        generateResumePreview(resumeData);
        
        // Show preview section
        showPreviewSection();
    });
    
    // Generate resume preview
    function generateResumePreview(data) {
        // Create resume HTML
        const resumeHTML = `
            <div class="resume-header">
                <h2>${data.name}</h2>
                <p>${data.email} | ${data.phone}</p>
            </div>
            
            ${data.summary ? `
            <div class="resume-section">
                <h3>Professional Summary</h3>
                <p>${data.summary}</p>
            </div>
            ` : ""}
            
            ${data.experience ? `
            <div class="resume-section">
                <h3>Experience</h3>
                <p>${data.experience.replace(/\n/g, "<br>")}</p>
            </div>
            ` : ""}
            
            ${data.education ? `
            <div class="resume-section">
                <h3>Education</h3>
                <p>${data.education.replace(/\n/g, "<br>")}</p>
            </div>
            ` : ""}
            
            ${data.skills.length > 0 ? `
            <div class="resume-section">
                <h3>Skills</h3>
                <div class="resume-skills">
                    ${data.skills.map(skill => `<span class="resume-skill">${skill}</span>`).join("")}
                </div>
            </div>
            ` : ""}
        `;
        
        // Insert into preview
        resumePreview.innerHTML = resumeHTML;
    }
    
    // Edit resume button
    editResumeBtn.addEventListener("click", function() {
        showBuilderSection();
    });
    
    // Download resume button - using html2pdf.js
    downloadResumeBtn.addEventListener("click", function() {
        // In a real application, you would use a library like html2pdf.js
        // For this example, we'll just show an alert
        alert("In a real application, this would download a PDF of your resume.");
        
        // Example using html2pdf.js (would need to include the library)
        // html2pdf().from(resumePreview).save("resume.pdf");
    });
});
