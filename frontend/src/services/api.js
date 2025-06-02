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

/**
 * Analyzes a resume file by uploading it to the backend.
 * @param {FormData} formData - The FormData object containing the resume file.
 * The file should be appended under the key 'file'.
 * @returns {Promise<import('axios').AxiosResponse<any>>} A promise that resolves with the server's response,
 * typically containing the parsed resume data as JSON.
 */
export const analyzeResume = (formData) => {
    // formData should be a FormData object with the file
    return apiClient.post('/resume/analyze', formData, {
        headers: {
            'Content-Type': 'multipart/form-data', // Important for file uploads
        },
    });
};

// --- Job Analysis ---

/**
 * Scrapes job description text from a given URL via the backend.
 * @param {string} url - The URL of the job description page to scrape.
 * @returns {Promise<import('axios').AxiosResponse<any>>} A promise that resolves with the server's response,
 * typically containing the scraped text.
 */
export const scrapeJobUrl = (url) => {
    return apiClient.post('/job/scrape-url', { url });
};

/**
 * Sends raw job description text to the backend for analysis or storage.
 * @param {string} text - The raw job description text.
 * @returns {Promise<import('axios').AxiosResponse<any>>} A promise that resolves with the server's response.
 */
export const analyzeJobText = (text) => {
    return apiClient.post('/job/analyze-text', { text });
};

/**
 * Compares resume data with job description text via the backend.
 * @param {string} [jobDescriptionText] - Optional. The job description text. If not provided,
 * the backend might use a previously stored/analyzed job description.
 * @param {object} [resumeData] - Optional. The structured resume data. If not provided,
 * the backend might use a previously stored/analyzed resume.
 * @returns {Promise<import('axios').AxiosResponse<any>>} A promise that resolves with the server's response,
 * typically containing comparison results (matching skills, missing skills, score).
 */
export const compareResumeWithJob = (jobDescriptionText, resumeData) => {
    // resumeData is optional; if null/undefined, backend uses its last analyzed resume
    // jobDescriptionText is also optional by backend logic if previously stored
    const payload = {};
    if (jobDescriptionText) payload.job_description_text = jobDescriptionText;
    if (resumeData) payload.resume_data = resumeData;
    return apiClient.post('/job/compare-resume', payload);
};

// --- Resume Builder ---

/**
 * Retrieves the current resume data from the backend's builder state.
 * @returns {Promise<import('axios').AxiosResponse<any>>} A promise that resolves with the server's response,
 * typically containing the current resume data as JSON.
 */
export const getResumeData = () => {
    return apiClient.get('/builder/resume');
};

/**
 * Updates the resume data on the backend with the provided data.
 * @param {object} resumeData - The full resume data object to update.
 * @returns {Promise<import('axios').AxiosResponse<any>>} A promise that resolves with the server's response,
 * typically a confirmation message.
 */
export const updateResumeData = (resumeData) => {
    return apiClient.put('/builder/resume', resumeData);
};

/**
 * Requests a PDF download of the resume from the backend.
 * @param {object} [resumeData=null] - Optional. If provided, this specific resume data will be used
 * to generate the PDF. Otherwise, the backend uses its current resume state.
 * @returns {Promise<import('axios').AxiosResponse<Blob>>} A promise that resolves with the server's response,
 * containing the PDF file as a Blob.
 */
export const downloadResumePdf = (resumeData = null) => {
    // resumeData is optional. If provided, it's sent to generate PDF from that specific data.
    // Otherwise, backend generates PDF from its current state.
    const payload = resumeData ? { resume_data: resumeData } : null;
    return apiClient.post('/builder/resume/download-pdf', payload, {
        responseType: 'blob', // Important for file downloads, tells Axios to expect a binary blob
    });
};

export default apiClient;
