// frontend/src/components/ResumeBuilderPage.js
import React, { useState, useEffect, useCallback } from 'react';
import { getResumeData, updateResumeData, downloadResumePdf } from '../services/api';
import './ResumeBuilderPage.css'; // We'll create this

// Helper to download blob data
const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
};

const ResumeBuilderPage = () => {
    const [resumeData, setResumeData] = useState(null); // Will hold the entire resume object
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const [error, setError] = useState('');
    const [saveSuccess, setSaveSuccess] = useState('');

    const loadResumeData = useCallback(async () => {
        setIsLoading(true);
        setError('');
        try {
            const response = await getResumeData();
            setResumeData(response.data);
        } catch (err) {
            handleApiError(err, "loading resume data");
            // If API fails, user will see an error.
            // The form rendering logic needs to handle resumeData being null initially.
        } finally {
            setIsLoading(false);
        }
    }, []); // Empty dependency array for useCallback as it doesn't depend on props/state from parent

    useEffect(() => {
        loadResumeData();
    }, [loadResumeData]); // Load data on component mount

    const handleInputChange = (event, section = null, index = null, field = null) => {
        const { name, value } = event.target;
        setSaveSuccess(''); // Clear save success message on new change

        if (section) {
            if (index !== null) { // Array item (e.g., experience, education)
                setResumeData(prev => ({
                    ...prev,
                    [section]: prev[section].map((item, i) =>
                        i === index ? { ...item, [field || name]: value } : item
                    )
                }));
            } else { // Object item (e.g., contact_info)
                setResumeData(prev => ({
                    ...prev,
                    [section]: {
                        ...prev[section],
                        [name]: value
                    }
                }));
            }
        } else { // Top-level field (e.g., name, summary)
            setResumeData(prev => ({
                ...prev,
                [name]: value
            }));
        }
    };

    // Specific handler for skills as it's a simple array of strings
    const handleSkillsChange = (event) => {
        setSaveSuccess('');
        // Assuming skills are comma-separated in a textarea or similar input
        const skillsArray = event.target.value.split(',').map(skill => skill.trim()).filter(skill => skill);
        setResumeData(prev => ({
            ...prev,
            skills: skillsArray
        }));
    };


    const handleSaveResume = async () => {
        if (!resumeData) {
            setError("No resume data to save.");
            return;
        }
        setIsSaving(true);
        setError('');
        setSaveSuccess('');
        try {
            await updateResumeData(resumeData);
            setSaveSuccess("Resume saved successfully!");
        } catch (err) {
            handleApiError(err, "saving resume data");
        } finally {
            setIsSaving(false);
        }
    };

    const handleDownloadPdf = async () => {
        if (!resumeData) {
            setError("No resume data available to generate PDF.");
            return;
        }
        setIsDownloading(true);
        setError('');
        try {
            // Send current state of resumeData for PDF generation
            const response = await downloadResumePdf(resumeData);
            downloadBlob(response.data, "resume.pdf");
        } catch (err) {
            handleApiError(err, "downloading PDF");
        } finally {
            setIsDownloading(false);
        }
    };

    const handleApiError = (err, actionContext) => {
        let errorMessage = `An error occurred during ${actionContext}.`;
        if (err.response) {
             if (typeof err.response.data === 'string') {
                errorMessage = err.response.data;
            } else if (err.response.data && err.response.data.detail) {
                errorMessage = err.response.data.detail;
            } else if (err.response.data && err.response.data.message) {
                errorMessage = err.response.data.message;
            } else if (err.response.data instanceof Blob) { // Handle error responses that are blobs
                err.response.data.text().then(text => {
                    try {
                        const errorJson = JSON.parse(text);
                        setError(errorJson.detail || `Error ${err.response.status} (${actionContext})`);
                    } catch (parseErr) {
                        setError(`Error ${err.response.status} (${actionContext}): Could not parse error response.`);
                    }
                }).catch(() => {
                    setError(`Error ${err.response.status} (${actionContext}): Non-JSON error blob.`);
                });
                return; // Early exit as error setting is async
            }
             else {
                errorMessage = `Error ${err.response.status} (${actionContext}): ${err.response.statusText}`;
            }
        } else if (err.request) {
            errorMessage = `Network error during ${actionContext}. Could not connect to the server.`;
        } else {
            errorMessage = err.message;
        }
        setError(errorMessage);
        setSaveSuccess('');
        console.error(`Resume Builder Error (${actionContext}):`, err);
    };


    if (isLoading) {
        return <div className="page-content loading-spinner">Loading Resume Builder...</div>;
    }

    if (error && !resumeData) { // Critical error on load and no data to show form
        return (
            <div className="page-content error-message">
                Error: {error} <button onClick={loadResumeData} disabled={isLoading}>Try Again</button>
            </div>
        );
    }

    if (!resumeData) {
        // This should ideally not be reached if loadResumeData is called on mount and handles its state.
        // However, as a fallback if resumeData is still null.
        return (
            <div className="page-content error-message">
                Could not load resume data. Please try refreshing the page or click
                <button onClick={loadResumeData} disabled={isLoading} style={{marginLeft: '10px'}}>Reload Data</button>.
            </div>
        );
    }


    return (
        <div className="page-content resume-builder-page">
            <h2>Resume Builder</h2>
            <p>Create or edit your professional resume. Click "Save Resume" to persist your changes on the server (in-memory for this demo) and "Download PDF" to get your resume.</p>

            {error && <p className="error-message">Error: {error}</p>}
            {saveSuccess && <p className="success-message">{saveSuccess}</p>}

            <div className="resume-form-actions">
                <button onClick={handleSaveResume} disabled={isSaving || isLoading}>
                    {isSaving ? 'Saving...' : 'Save Resume'}
                </button>
                <button onClick={handleDownloadPdf} disabled={isDownloading || isLoading}>
                    {isDownloading ? 'Downloading...' : 'Download PDF'}
                </button>
            </div>

            <form className="resume-form" onSubmit={(e) => e.preventDefault()}>
                {/* Personal Information Section */}
                <fieldset>
                    <legend>Personal Information</legend>
                    <div className="form-grid">
                        <div className="form-group">
                            <label htmlFor="name">Full Name:</label>
                            <input type="text" id="name" name="name" value={resumeData.name || ''} onChange={handleInputChange} />
                        </div>
                         <div className="form-group">
                            <label htmlFor="email">Email:</label>
                            <input type="email" id="email" name="email" value={resumeData.contact_info?.email || ''} onChange={(e) => handleInputChange(e, 'contact_info')} />
                        </div>
                        <div className="form-group">
                            <label htmlFor="phone">Phone:</label>
                            <input type="tel" id="phone" name="phone" value={resumeData.contact_info?.phone || ''} onChange={(e) => handleInputChange(e, 'contact_info')} />
                        </div>
                        <div className="form-group">
                            <label htmlFor="linkedin">LinkedIn Profile URL:</label>
                            <input type="url" id="linkedin" name="linkedin" value={resumeData.contact_info?.linkedin || ''} onChange={(e) => handleInputChange(e, 'contact_info')} placeholder="linkedin.com/in/yourprofile"/>
                        </div>
                        <div className="form-group">
                            <label htmlFor="github">GitHub Profile URL:</label>
                            <input type="url" id="github" name="github" value={resumeData.contact_info?.github || ''} onChange={(e) => handleInputChange(e, 'contact_info')} placeholder="github.com/yourusername"/>
                        </div>
                         <div className="form-group full-width">
                            <label htmlFor="address">Address:</label>
                            <input type="text" id="address" name="address" value={resumeData.contact_info?.address || ''} onChange={(e) => handleInputChange(e, 'contact_info')} />
                        </div>
                    </div>
                </fieldset>

                {/* Summary Section */}
                <fieldset>
                    <legend>Summary</legend>
                    <div className="form-group">
                        <textarea id="summary" name="summary" value={resumeData.summary || ''} onChange={handleInputChange} rows="5" placeholder="Write a brief professional summary..."></textarea>
                    </div>
                </fieldset>

                {/* Skills Section (Simple Textarea for Comma-Separated Skills) */}
                <fieldset>
                    <legend>Skills</legend>
                    <div className="form-group">
                        <label htmlFor="skills">Skills (comma-separated):</label>
                        <textarea
                            id="skills"
                            name="skills"
                            value={(resumeData.skills || []).join(', ')}
                            onChange={handleSkillsChange}
                            rows="3"
                            placeholder="e.g., Python, JavaScript, Project Management"
                        />
                    </div>
                </fieldset>

                {/* Placeholders for Experience, Education, Projects - To be implemented next */}
                <fieldset>
                    <legend>Experience</legend>
                    <p className="placeholder-text">Experience section form will be here.</p>
                </fieldset>
                <fieldset>
                    <legend>Education</legend>
                    <p className="placeholder-text">Education section form will be here.</p>
                </fieldset>
                <fieldset>
                    <legend>Projects</legend>
                    <p className="placeholder-text">Projects section form will be here.</p>
                </fieldset>

            </form>
             <div className="resume-form-actions bottom-actions">
                <button onClick={handleSaveResume} disabled={isSaving || isLoading}>
                    {isSaving ? 'Saving...' : 'Save Resume'}
                </button>
                <button onClick={handleDownloadPdf} disabled={isDownloading || isLoading}>
                    {isDownloading ? 'Downloading...' : 'Download PDF'}
                </button>
            </div>
        </div>
    );
};

export default ResumeBuilderPage;
