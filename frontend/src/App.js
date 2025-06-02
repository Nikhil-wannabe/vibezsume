// frontend/src/App.js
import React, { useState } from 'react';
import './App.css';
import ResumeAnalyzerPage from './components/ResumeAnalyzerPage';
import JobAnalyzerPage from './components/JobAnalyzerPage';
import ResumeBuilderPage from './components/ResumeBuilderPage'; // Import new component

// Placeholder for Settings page component
const Settings = () => <div className="page-content"><h2>Settings</h2><p>Application settings.</p></div>;

function App() {
    // State variable to track the currently active page.
    // Defaults to 'analyzer' (Resume Analyzer page).
    const [currentPage, setCurrentPage] = useState('analyzer');

    // Function to conditionally render the component based on the currentPage state.
    const renderPage = () => {
        switch (currentPage) {
            case 'analyzer':
                return <ResumeAnalyzerPage />;
            case 'job':
                return <JobAnalyzerPage />;
            case 'builder':
                return <ResumeBuilderPage />; // Use the actual ResumeBuilderPage component
            case 'settings':
                return <Settings />;
            default:
                // Fallback to Resume Analyzer page if currentPage is unknown.
                return <ResumeAnalyzerPage />;
        }
    };

    // Navigation button handlers: Each button updates the currentPage state to display the corresponding page.
    return (
        <div className="App">
            <header className="App-header">
                <h1>AI Resume Toolkit</h1>
                <nav>
                    {/* Button to navigate to the Resume Analyzer page */}
                    <button onClick={() => setCurrentPage('analyzer')} className={currentPage === 'analyzer' ? 'active' : ''}>Resume Analyzer</button>
                    {/* Button to navigate to the Job Analyzer page */}
                    <button onClick={() => setCurrentPage('job')} className={currentPage === 'job' ? 'active' : ''}>Job Analyzer</button>
                    {/* Button to navigate to the Resume Builder page */}
                    <button onClick={() => setCurrentPage('builder')} className={currentPage === 'builder' ? 'active' : ''}>Resume Builder</button>
                    {/* Button to navigate to the Settings page */}
                    <button onClick={() => setCurrentPage('settings')} className={currentPage === 'settings' ? 'active' : ''}>Settings</button>
                </nav>
            </header>
            <main>
                {/* Renders the component returned by renderPage() */}
                {renderPage()}
            </main>
            <footer>
                <p>&copy; 2023 AI Resume Toolkit</p>
            </footer>
        </div>
    );
}

export default App;
