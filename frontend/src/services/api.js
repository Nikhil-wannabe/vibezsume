// frontend/src/services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// --- Resume Analysis ---
export const analyzeResume = (formData) => {
    // formData should be a FormData object with the file
    return apiClient.post('/resume/analyze', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
};

// --- Job Analysis ---
export const scrapeJobUrl = (url) => {
    return apiClient.post('/job/scrape-url', { url });
};

export const analyzeJobText = (text) => {
    return apiClient.post('/job/analyze-text', { text });
};

export const compareResumeWithJob = (jobDescriptionText, resumeData) => {
    // resumeData is optional; if null/undefined, backend uses its last analyzed resume
    // jobDescriptionText is also optional by backend logic if previously stored
    const payload = {};
    if (jobDescriptionText) payload.job_description_text = jobDescriptionText;
    if (resumeData) payload.resume_data = resumeData;
    return apiClient.post('/job/compare-resume', payload);
};

// --- Resume Builder ---
export const getResumeData = () => {
    return apiClient.get('/builder/resume');
};

export const updateResumeData = (resumeData) => {
    return apiClient.put('/builder/resume', resumeData);
};

export const downloadResumePdf = (resumeData = null) => {
    // resumeData is optional. If provided, it's sent to generate PDF from that specific data.
    // Otherwise, backend generates PDF from its current state.
    const payload = resumeData ? { resume_data: resumeData } : null;
    return apiClient.post('/builder/resume/download-pdf', payload, {
        responseType: 'blob', // Important for file downloads
    });
};

export default apiClient;
