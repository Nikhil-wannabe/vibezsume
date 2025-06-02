// frontend/src/components/JobAnalyzerPage.js
import React, { useState, useEffect } from 'react';
import { scrapeJobUrl, analyzeJobText, compareResumeWithJob } from '../services/api';
import './JobAnalyzerPage.css'; // We'll create this

const JobAnalyzerPage = () => {
    const [jobUrl, setJobUrl] = useState('');
    const [jobText, setJobText] = useState('');
    const [processedJobText, setProcessedJobText] = useState(''); // Text after scraping or direct input
    const [comparisonResult, setComparisonResult] = useState(null);
    const [isLoadingScrape, setIsLoadingScrape] = useState(false);
    const [isLoadingText, setIsLoadingText] = useState(false);
    const [isLoadingCompare, setIsLoadingCompare] = useState(false);
    const [error, setError] = useState('');

    // Effect to clear comparison if job text changes
    useEffect(() => {
        setComparisonResult(null);
    }, [processedJobText]);

    const handleUrlSubmit = async (event) => {
        event.preventDefault();
        if (!jobUrl) {
            setError('Please enter a Job URL.');
            return;
        }
        setIsLoadingScrape(true);
        setError('');
        setProcessedJobText('');
        try {
            const response = await scrapeJobUrl(jobUrl);
            setProcessedJobText(response.data.scraped_text);
        } catch (err) {
            handleApiError(err, 'scraping job URL');
        } finally {
            setIsLoadingScrape(false);
        }
    };

    const handleTextSubmit = async (event) => {
        event.preventDefault();
        if (!jobText) {
            setError('Please paste or type job description text.');
            return;
        }
        setIsLoadingText(true);
        setError('');
        try {
            // The API stores this text on the backend.
            // We'll just use the input `jobText` directly for display and comparison trigger.
            await analyzeJobText(jobText);
            setProcessedJobText(jobText);
        } catch (err) {
             handleApiError(err, 'analyzing job text');
        } finally {
            setIsLoadingText(false);
        }
    };

    const handleCompare = async () => {
        if (!processedJobText) {
            setError('Please analyze a job description first (either via URL or text).');
            return;
        }
        setIsLoadingCompare(true);
        setError('');
        setComparisonResult(null);
        try {
            // API will use last analyzed resume if resumeData is not sent
            // It will use last processed job text if jobDescriptionText is not sent
            // For clarity, we send the current processedJobText.
            const response = await compareResumeWithJob(processedJobText, null);
            setComparisonResult(response.data);
        } catch (err) {
            handleApiError(err, 'comparing resume with job description');
        } finally {
            setIsLoadingCompare(false);
        }
    };

    const handleApiError = (err, actionContext) => {
        let errorMessage = `An error occurred during ${actionContext}.`;
        if (err.response) {
            if (typeof err.response.data === 'string') {
                errorMessage = err.response.data;
            } else if (err.response.data && err.response.data.detail) {
                errorMessage = err.response.data.detail;
            } else {
                errorMessage = `Error ${err.response.status} (${actionContext}): ${err.response.statusText}`;
            }
        } else if (err.request) {
            errorMessage = `Network error during ${actionContext}. Could not connect to the server.`;
        } else {
            errorMessage = err.message;
        }
        setError(errorMessage);
        console.error(`Job Analyzer Error (${actionContext}):`, err);
    };

    const renderComparisonResult = (data) => {
        if (!data) return null;
        return (
            <div className="comparison-results-container">
                <h4>Comparison with Last Analyzed Resume:</h4>
                <p><strong>Match Score (Heuristic):</strong> {data.match_score_heuristic !== undefined ? data.match_score_heuristic + '%' : 'N/A'}</p>

                <h5>Matching Skills:</h5>
                {data.matching_skills && data.matching_skills.length > 0 ? (
                    <ul>{data.matching_skills.map(skill => <li key={skill} className="skill-match">{skill}</li>)}</ul>
                ) : <p>No direct skill matches found based on keywords.</p>}

                <h5>Potential Missing Skills (from Job Description keywords):</h5>
                {data.missing_skills_from_jd && data.missing_skills_from_jd.length > 0 ? (
                    <ul>{data.missing_skills_from_jd.map(skill => <li key={skill} className="skill-missing">{skill}</li>)}</ul>
                ) : <p>No specific missing skill keywords identified, or all covered.</p>}

                <h5>Job Summary Keywords (Top 20):</h5>
                {data.job_summary_keywords && data.job_summary_keywords.length > 0 ? (
                    <p className="keywords-list">{data.job_summary_keywords.join(', ')}</p>
                ) : <p>No keywords extracted from job description.</p>}
            </div>
        );
    };

    return (
        <div className="page-content job-analyzer-page">
            <h2>Job Analyzer</h2>
            <p>Analyze a job description by providing a URL or pasting the text directly. Then, compare it against your last analyzed resume.</p>

            <div className="job-input-section">
                <form onSubmit={handleUrlSubmit} className="analyzer-form inline-form">
                    <div className="form-group">
                        <label htmlFor="jobUrl">Job Posting URL:</label>
                        <input
                            type="url"
                            id="jobUrl"
                            value={jobUrl}
                            onChange={(e) => { setJobUrl(e.target.value); setError(''); }}
                            placeholder="https://example.com/job/123"
                        />
                    </div>
                    <button type="submit" disabled={isLoadingScrape || isLoadingText}>
                        {isLoadingScrape ? 'Scraping...' : 'Scrape & Analyze URL'}
                    </button>
                </form>

                <p className="or-divider">OR</p>

                <form onSubmit={handleTextSubmit} className="analyzer-form">
                    <div className="form-group">
                        <label htmlFor="jobText">Paste Job Description Text:</label>
                        <textarea
                            id="jobText"
                            value={jobText}
                            onChange={(e) => { setJobText(e.target.value); setError(''); }}
                            rows="10"
                            placeholder="Paste the full job description here..."
                        />
                    </div>
                    <button type="submit" disabled={isLoadingText || isLoadingScrape}>
                        {isLoadingText ? 'Analyzing...' : 'Analyze Pasted Text'}
                    </button>
                </form>
            </div>

            {error && <p className="error-message">Error: {error}</p>}

            {processedJobText && (
                <div className="processed-job-text-container">
                    <h3>Processed Job Description:</h3>
                    <pre className="job-text-display">{processedJobText}</pre>
                    <button onClick={handleCompare} disabled={isLoadingCompare} className="compare-button">
                        {isLoadingCompare ? 'Comparing...' : 'Compare with Last Resume'}
                    </button>
                </div>
            )}

            {isLoadingCompare && <div className="loading-spinner">Comparing...</div>}
            {comparisonResult && renderComparisonResult(comparisonResult)}
        </div>
    );
};

export default JobAnalyzerPage;
