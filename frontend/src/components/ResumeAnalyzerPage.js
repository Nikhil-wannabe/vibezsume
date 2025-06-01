// frontend/src/components/ResumeAnalyzerPage.js
import React, { useState } from 'react';
import { analyzeResume } from '../services/api';
import './ResumeAnalyzerPage.css'; // We'll create this for styling

const ResumeAnalyzerPage = () => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
        setAnalysisResult(null); // Reset previous results
        setError('');
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!selectedFile) {
            setError('Please select a file first.');
            return;
        }

        setIsLoading(true);
        setError('');
        setAnalysisResult(null);

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await analyzeResume(formData);
            setAnalysisResult(response.data);
        } catch (err) {
            let errorMessage = 'An error occurred during analysis.';
            if (err.response) {
                // API errors (e.g., 4xx, 5xx)
                if (typeof err.response.data === 'string') {
                    errorMessage = err.response.data;
                } else if (err.response.data && err.response.data.detail) {
                     errorMessage = err.response.data.detail;
                } else {
                    errorMessage = `Error ${err.response.status}: ${err.response.statusText}`;
                }
            } else if (err.request) {
                // Network errors (e.g., backend down)
                errorMessage = 'Network error. Could not connect to the server.';
            } else {
                // Other errors
                errorMessage = err.message;
            }
            setError(errorMessage);
            console.error("Analysis error:", err);
        } finally {
            setIsLoading(false);
        }
    };

    const renderAnalysisResult = (data) => {
        if (!data) return null;

        // Helper to render nested objects/arrays nicely
        const renderNested = (nestedData, indentLevel = 0) => {
            if (nestedData === null || nestedData === undefined) return <span className="json-null">null</span>;
            if (typeof nestedData === 'string') return <span className="json-string">"{nestedData}"</span>;
            if (typeof nestedData === 'number') return <span className="json-number">{nestedData}</span>;
            if (typeof nestedData === 'boolean') return <span className="json-boolean">{String(nestedData)}</span>;

            if (Array.isArray(nestedData)) {
                return (
                    <>
                        [
                        {nestedData.map((item, index) => (
                            <div key={index} style={{ marginLeft: `${(indentLevel + 1) * 20}px` }}>
                                {renderNested(item, indentLevel + 1)}
                                {index < nestedData.length - 1 ? ',' : ''}
                            </div>
                        ))}
                        <div style={{ marginLeft: `${indentLevel * 20}px` }}>]</div>
                    </>
                );
            }

            if (typeof nestedData === 'object') {
                return (
                    <>
                        {'{'}
                        {Object.entries(nestedData).map(([key, value], index, arr) => (
                            <div key={key} style={{ marginLeft: `${(indentLevel + 1) * 20}px` }}>
                                <strong className="json-key">"{key}"</strong>: {renderNested(value, indentLevel + 1)}
                                {index < arr.length - 1 ? ',' : ''}
                            </div>
                        ))}
                        <div style={{ marginLeft: `${indentLevel * 20}px` }}>{'}'}</div>
                    </>
                );
            }
            return String(nestedData);
        };

        return (
            <div className="analysis-results-container">
                <h3>Analysis Results:</h3>
                <pre className="json-display">
                    {renderNested(data)}
                </pre>
            </div>
        );
    };


    return (
        <div className="page-content resume-analyzer-page">
            <h2>Resume Analyzer</h2>
            <p>Upload your resume (PDF, DOCX, or TXT) to extract structured information using our SLM.</p>

            <form onSubmit={handleSubmit} className="analyzer-form">
                <div className="form-group">
                    <label htmlFor="resumeFile">Choose Resume File:</label>
                    <input
                        type="file"
                        id="resumeFile"
                        onChange={handleFileChange}
                        accept=".pdf,.doc,.docx,.txt"
                    />
                </div>
                <button type="submit" disabled={isLoading || !selectedFile}>
                    {isLoading ? 'Analyzing...' : 'Analyze Resume'}
                </button>
            </form>

            {error && <p className="error-message">Error: {error}</p>}

            {isLoading && <div className="loading-spinner">Processing...</div>}

            {analysisResult && renderAnalysisResult(analysisResult)}
        </div>
    );
};

export default ResumeAnalyzerPage;
