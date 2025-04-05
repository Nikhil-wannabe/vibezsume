document.addEventListener("DOMContentLoaded", function() {
    // DOM Elements - Navigation
    const homeSection = document.getElementById("home-section");
    const builderSection = document.getElementById("builder-section");
    const previewSection = document.getElementById("preview-section");
    const analyzerSection = document.getElementById("analyzer-section");
    const jobDescriptionSection = document.getElementById("job-description-section");
    
    const homeLink = document.getElementById("home-link");
    const builderLink = document.getElementById("builder-link");
    const analyzerLink = document.getElementById("analyzer-link");
    const jobLink = document.getElementById("job-link");
    const startBuilderBtn = document.getElementById("start-builder");
    const startAnalyzerBtn = document.getElementById("start-analyzer");
    
    // DOM Elements - Resume Builder
    const resumeForm = document.getElementById("resume-form");
    const formSteps = document.querySelectorAll(".form-step");
    const progressSteps = document.querySelectorAll(".progress-bar .step");
    
    const nextBtns = document.querySelectorAll(".next-btn");
    const prevBtns = document.querySelectorAll(".prev-btn");
    
    const skillInput = document.getElementById("skill-input");
    const addSkillBtn = document.getElementById("add-skill-btn");
    const skillsList = document.getElementById("skills-list");
    const skillsInput = document.getElementById("skills");
    
    // DOM Elements - Preview
    const editResumeBtn = document.getElementById("edit-resume-btn");
    const downloadResumeBtn = document.getElementById("download-resume-btn");
    const resumePreview = document.getElementById("resume-preview");
    
    // DOM Elements - Resume Analyzer
    const resumeUploadForm = document.getElementById("resume-upload-form");
    const uploadStatus = document.getElementById("upload-status");
    const analysisResults = document.getElementById("analysis-results");
    const resumeDataContainer = document.getElementById("resume-data");
    const jobMatchesList = document.getElementById("job-matches-list");
    const editExtractedBtn = document.getElementById("edit-extracted-btn");
    
    // DOM Elements - Job Description
    const jobDescriptionForm = document.getElementById("job-description-form");
    const jobAnalysisStatus = document.getElementById("job-analysis-status");
    const jobAnalysisResults = document.getElementById("job-analysis-results");
    const jobDataContainer = document.getElementById("job-data");
    const skillRequirementsList = document.getElementById("skill-requirements-list");
    const matchResumeBtn = document.getElementById("match-resume-btn");
    const matchResumeStatus = document.getElementById("match-resume-status");
    const resumeJobMatch = document.getElementById("resume-job-match");
    
    // State variables
    let currentStep = 1;
    let skills = [];
    let extractedResumeData = null;
    let currentJobId = null;
    
    // Navigation between sections
    homeLink.addEventListener("click", function(e) {
        e.preventDefault();
        showHomeSection();
    });
    
    builderLink.addEventListener("click", function(e) {
        e.preventDefault();
        showBuilderSection();
    });
    
    analyzerLink.addEventListener("click", function(e) {
        e.preventDefault();
        showAnalyzerSection();
    });
    
    jobLink.addEventListener("click", function(e) {
        e.preventDefault();
        showJobDescriptionSection();
    });
    
    startBuilderBtn.addEventListener("click", function() {
        showBuilderSection();
    });
    
    startAnalyzerBtn.addEventListener("click", function() {
        showAnalyzerSection();
    });
    
    if (editExtractedBtn) {
        editExtractedBtn.addEventListener("click", function() {
            // Fill form with extracted data
            fillFormWithExtractedData();
            showBuilderSection();
        });
    }
    
    function showHomeSection() {
        homeSection.classList.remove("hidden");
        builderSection.classList.add("hidden");
        previewSection.classList.add("hidden");
        analyzerSection.classList.add("hidden");
        jobDescriptionSection.classList.add("hidden");
        
        homeLink.classList.add("active");
        builderLink.classList.remove("active");
        analyzerLink.classList.remove("active");
        jobLink.classList.remove("active");
    }
    
    function showBuilderSection() {
        homeSection.classList.add("hidden");
        builderSection.classList.remove("hidden");
        previewSection.classList.add("hidden");
        analyzerSection.classList.add("hidden");
        jobDescriptionSection.classList.add("hidden");
        
        homeLink.classList.remove("active");
        builderLink.classList.add("active");
        analyzerLink.classList.remove("active");
        jobLink.classList.remove("active");
    }
    
    function showPreviewSection() {
        homeSection.classList.add("hidden");
        builderSection.classList.add("hidden");
        previewSection.classList.remove("hidden");
        analyzerSection.classList.add("hidden");
        jobDescriptionSection.classList.add("hidden");
        
        homeLink.classList.remove("active");
        builderLink.classList.add("active");
        analyzerLink.classList.remove("active");
        jobLink.classList.remove("active");
    }
    
    function showAnalyzerSection() {
        homeSection.classList.add("hidden");
        builderSection.classList.add("hidden");
        previewSection.classList.add("hidden");
        analyzerSection.classList.remove("hidden");
        jobDescriptionSection.classList.add("hidden");
        
        homeLink.classList.remove("active");
        builderLink.classList.remove("active");
        analyzerLink.classList.add("active");
        jobLink.classList.remove("active");
    }
    
    function showJobDescriptionSection() {
        homeSection.classList.add("hidden");
        builderSection.classList.add("hidden");
        previewSection.classList.add("hidden");
        analyzerSection.classList.add("hidden");
        jobDescriptionSection.classList.remove("hidden");
        
        homeLink.classList.remove("active");
        builderLink.classList.remove("active");
        analyzerLink.classList.remove("active");
        jobLink.classList.add("active");
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
    
    // Form submission for generating resume
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
        
        // Generate resume preview locally
        generateResumePreview(resumeData);
        
        // Also send to API to generate resume
        buildResumeWithAPI(resumeData);
        
        // Show preview section
        showPreviewSection();
    });
    
    async function buildResumeWithAPI(resumeData) {
        try {
            const response = await fetch('/resume/build', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(resumeData)
            });
            
            if (!response.ok) {
                throw new Error('Failed to build resume with API');
            }
            
            const result = await response.json();
            console.log('Resume built successfully:', result);
            
            // Store the generated ID for download
            if (result.generated_id) {
                downloadResumeBtn.setAttribute('data-id', result.generated_id);
            }
            
        } catch (error) {
            console.error('Error building resume:', error);
        }
    }
    
    // Generate resume preview locally
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
    
    // Download resume button
    downloadResumeBtn.addEventListener("click", async function() {
        const resumeId = downloadResumeBtn.getAttribute('data-id');
        
        if (!resumeId) {
            // Fallback to collecting data if no ID
            const resumeData = {
                name: document.getElementById("name").value,
                email: document.getElementById("email").value,
                phone: document.getElementById("phone").value,
                experience: document.getElementById("experience").value,
                education: document.getElementById("education").value,
                skills: skills,
                summary: document.getElementById("summary").value
            };
            
            try {
                const response = await fetch('/resume/generate-pdf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(resumeData)
                });
                
                if (!response.ok) {
                    throw new Error('Failed to generate PDF');
                }
                
                const result = await response.json();
                
                // Create a download link for the PDF
                if (result.pdf_base64) {
                    const pdfBlob = base64ToBlob(result.pdf_base64, 'application/pdf');
                    const url = URL.createObjectURL(pdfBlob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${resumeData.name.replace(/\s+/g, '_')}_resume.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }
                
            } catch (error) {
                console.error('Error downloading resume:', error);
                alert('Failed to download resume. Please try again.');
            }
        } else {
            // If we have an ID, use it to get the PDF
            window.open(`/resume/download/${resumeId}`, '_blank');
        }
    });
    
    // Convert base64 to Blob
    function base64ToBlob(base64, mimeType) {
        const byteCharacters = atob(base64);
        const byteArrays = [];
        
        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
            const slice = byteCharacters.slice(offset, offset + 512);
            
            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }
            
            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }
        
        return new Blob(byteArrays, {type: mimeType});
    }
    
    // Resume upload and parsing
    if (resumeUploadForm) {
        resumeUploadForm.addEventListener("submit", async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById("resume-file");
            if (!fileInput.files || fileInput.files.length === 0) {
                uploadStatus.textContent = "Please select a file to upload";
                uploadStatus.className = "error";
                return;
            }
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append("file", file);
            
            uploadStatus.textContent = "Uploading and analyzing your resume...";
            uploadStatus.className = "";
            
            try {
                // Upload and parse resume
                const response = await fetch("/resume/upload", {
                    method: "POST",
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error("Failed to upload resume");
                }
                
                // Get parsed resume data
                const parsedData = await response.json();
                extractedResumeData = parsedData;
                
                // Display extracted information
                displayExtractedInfo(parsedData);
                
                // Match against job roles
                const jobMatches = await matchResumeToJobs(parsedData);
                
                // Display job matches
                displayJobMatches(jobMatches);
                
                // Show results
                analysisResults.classList.remove("hidden");
                
                uploadStatus.textContent = "Resume analyzed successfully!";
                uploadStatus.className = "success";
                
                if (extractedResumeData && currentJobId) {
                    enableResumeMatching();
                }
                
            } catch (error) {
                console.error("Error analyzing resume:", error);
                uploadStatus.textContent = "Error: " + error.message;
                uploadStatus.className = "error";
            }
        });
    }
    
    // Match resume to jobs
    async function matchResumeToJobs(resumeData) {
        try {
            // Use the actual job descriptions from your system or sample ones
            const sampleJobs = [
                "Software Engineer with expertise in Python, JavaScript, and web development",
                "Data Scientist with machine learning and statistical analysis skills",
                "DevOps Engineer familiar with cloud platforms and CI/CD pipelines"
            ];
            
            const response = await fetch("/resume/match-jobs", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    parsed_resume: resumeData,
                    job_descriptions: sampleJobs
                })
            });
            
            if (!response.ok) {
                throw new Error("Failed to match resume to jobs");
            }
            
            return await response.json();
            
        } catch (error) {
            console.error("Error matching jobs:", error);
            return [];
        }
    }
    
    // Display extracted resume information
    function displayExtractedInfo(data) {
        if (!resumeDataContainer) return;
        
        let html = "";
        
        if (data.name) {
            html += `<div class="resume-data-item"><strong>Name</strong> ${data.name}</div>`;
        }
        
        if (data.email) {
            html += `<div class="resume-data-item"><strong>Email</strong> ${data.email}</div>`;
        }
        
        if (data.phone) {
            html += `<div class="resume-data-item"><strong>Phone</strong> ${data.phone}</div>`;
        }
        
        if (data.skills && data.skills.length) {
            html += `
                <div class="resume-data-item">
                    <strong>Skills</strong>
                    <div class="resume-skills">
                        ${data.skills.map(skill => `<span class="resume-skill">${skill}</span>`).join("")}
                    </div>
                </div>
            `;
        }
        
        if (data.summary) {
            html += `<div class="resume-data-item"><strong>Summary</strong> ${data.summary}</div>`;
        }
        
        if (data.education) {
            html += `<div class="resume-data-item"><strong>Education</strong> ${data.education}</div>`;
        }
        
        if (data.experience) {
            html += `<div class="resume-data-item"><strong>Experience</strong> ${data.experience}</div>`;
        }
        
        resumeDataContainer.innerHTML = html;
    }
    
    // Display job matches
    function displayJobMatches(matches) {
        if (!jobMatchesList) return;
        
        if (!matches || matches.length === 0) {
            jobMatchesList.innerHTML = "<p>No job matches found</p>";
            return;
        }
        
        let html = "";
        
        matches.forEach(match => {
            // Determine match class based on score
            let matchClass = "weak";
            if (match.match_score >= 80) {
                matchClass = "excellent";
            } else if (match.match_score >= 60) {
                matchClass = "good";
            } else if (match.match_score >= 40) {
                matchClass = "moderate";
            }
            
            html += `
                <div class="job-match-card ${matchClass}">
                    <div class="job-match-title">${match.job_description}</div>
                    <div class="job-match-score">Match Score: ${match.match_score}%</div>
                    <div class="job-match-strength">${match.match_strength}</div>
                </div>
            `;
        });
        
        jobMatchesList.innerHTML = html;
    }
    
    // Display job information
    function displayJobInfo(jobData) {
        if (!jobDataContainer || !skillRequirementsList) return;
        
        // Display job title and basic info
        let jobHtml = `
            <div class="job-data-item">
                <strong>Job Title</strong>
                <p>${jobData.job_title}</p>
            </div>
            <div class="job-data-item">
                <strong>Description Preview</strong>
                <p>${jobData.description_preview}</p>
            </div>
        `;
        
        jobDataContainer.innerHTML = jobHtml;
        
        // Display skill requirements
        let skillsHtml = "";
        
        if (jobData.required_skills && jobData.required_skills.length > 0) {
            skillsHtml += `
                <div class="skills-section">
                    <h5>Required Skills</h5>
                    <div class="skills-list">
                        ${jobData.required_skills.map(skill => 
                            `<span class="skill-tag required">${skill}</span>`).join("")}
                    </div>
                </div>
            `;
        }
        
        if (jobData.nice_to_have && jobData.nice_to_have.length > 0) {
            skillsHtml += `
                <div class="skills-section">
                    <h5>Nice to Have</h5>
                    <div class="skills-list">
                        ${jobData.nice_to_have.map(skill => 
                            `<span class="skill-tag nice-to-have">${skill}</span>`).join("")}
                    </div>
                </div>
            `;
        }
        
        skillRequirementsList.innerHTML = skillsHtml;
    }
    
    // Enable resume matching
    function enableResumeMatching() {
        if (matchResumeBtn && matchResumeStatus) {
            matchResumeBtn.disabled = false;
            matchResumeStatus.textContent = "";
            
            matchResumeBtn.addEventListener("click", async function() {
                if (!currentJobId || !extractedResumeData) {
                    alert("Please upload a resume and analyze a job description first");
                    return;
                }
                
                try {
                    const response = await fetch("/resume/match-jobs", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            parsed_resume: extractedResumeData,
                            job_description_id: currentJobId
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error("Failed to match resume to job");
                    }
                    
                    const matches = await response.json();
                    if (matches && matches.length > 0) {
                        displayResumeJobMatch(matches[0]);
                    }
                    
                } catch (error) {
                    console.error("Error matching resume to job:", error);
                    alert("Error: " + error.message);
                }
            });
        }
    }
    
    // Display resume to job match
    function displayResumeJobMatch(match) {
        if (!resumeJobMatch) return;
        
        // Determine match class based on score
        let matchClass = "weak";
        if (match.match_score >= 80) {
            matchClass = "excellent";
        } else if (match.match_score >= 60) {
            matchClass = "good";
        } else if (match.match_score >= 40) {
            matchClass = "moderate";
        }
        
        let html = `
            <div class="match-result ${matchClass}">
                <h4>Match Result</h4>
                <div class="match-score">
                    <div class="score-value">${match.match_score}%</div>
                    <div class="score-label">${match.match_strength}</div>
                </div>
                
                <div class="match-details">
                    <div class="matched-skills">
                        <h5>Matching Skills</h5>
                        <div class="skills-list">
                            ${match.matched_required_skills.map(skill => 
                                `<span class="skill-tag matched required">${skill}</span>`).join("")}
                            ${match.matched_nice_to_have.map(skill => 
                                `<span class="skill-tag matched nice-to-have">${skill}</span>`).join("")}
                        </div>
                    </div>
                    
                    ${match.missing_required_skills.length > 0 ? `
                    <div class="missing-skills">
                        <h5>Missing Required Skills</h5>
                        <div class="skills-list">
                            ${match.missing_required_skills.map(skill => 
                                `<span class="skill-tag missing">${skill}</span>`).join("")}
                        </div>
                    </div>
                    ` : ''}
                    
                    ${match.recommendations.length > 0 ? `
                    <div class="recommendations">
                        <h5>Recommendations</h5>
                        <ul>
                            ${match.recommendations.map(rec => `<li>${rec}</li>`).join("")}
                        </ul>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        resumeJobMatch.innerHTML = html;
        resumeJobMatch.classList.remove("hidden");
    }
    
    // Job description handling
    if (jobDescriptionForm) {
        jobDescriptionForm.addEventListener("submit", async function(e) {
            e.preventDefault();
            
            const jobUrl = document.getElementById("job-url").value.trim();
            const jobDescription = document.getElementById("job-description").value.trim();
            
            if (!jobDescription) {
                jobAnalysisStatus.textContent = "Please enter a job description";
                jobAnalysisStatus.className = "error";
                return;
            }
            
            jobAnalysisStatus.textContent = "Analyzing job description...";
            jobAnalysisStatus.className = "";
            
            try {
                const response = await fetch("/resume/job-description", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        text: jobDescription,
                        url: jobUrl || null
                    })
                });
                
                if (!response.ok) {
                    throw new Error("Failed to analyze job description");
                }
                
                const result = await response.json();
                currentJobId = result.id;
                
                // Display job information
                displayJobInfo(result);
                
                // Show results
                jobAnalysisResults.classList.remove("hidden");
                
                // Enable resume matching if a resume is uploaded
                if (extractedResumeData) {
                    enableResumeMatching();
                }
                
                jobAnalysisStatus.textContent = "Job description analyzed successfully!";
                jobAnalysisStatus.className = "success";
                
            } catch (error) {
                console.error("Error analyzing job:", error);
                jobAnalysisStatus.textContent = "Error: " + error.message;
                jobAnalysisStatus.className = "error";
            }
        });
    }
});