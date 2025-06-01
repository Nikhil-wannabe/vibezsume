// frontend/src/App.js
import React, { useState } from 'react';
import './App.css';
import ResumeAnalyzerPage from './components/ResumeAnalyzerPage';
import JobAnalyzerPage from './components/JobAnalyzerPage';
import ResumeBuilderPage from './components/ResumeBuilderPage'; // Import new component

// const ResumeBuilder = () => <div className="page-content"><h2>Resume Builder</h2><p>Build your resume.</p></div>; // Remove this
const Settings = () => <div className="page-content"><h2>Settings</h2><p>Application settings.</p></div>;

function App() {
    const [currentPage, setCurrentPage] = useState('analyzer');

    const renderPage = () => {
        switch (currentPage) {
            case 'analyzer':
                return <ResumeAnalyzerPage />;
            case 'job':
                return <JobAnalyzerPage />;
            case 'builder':
                return <ResumeBuilderPage />; // Use the new component
            case 'settings':
                return <Settings />;
            default:
                return <ResumeAnalyzerPage />;
        }
    };

    // ... rest of App.js remains the same
    return (
        // ... same JSX structure as before ...
         <div className="App">
            <header className="App-header">
                <h1>AI Resume Toolkit</h1>
                <nav>
                    <button onClick={() => setCurrentPage('analyzer')} className={currentPage === 'analyzer' ? 'active' : ''}>Resume Analyzer</button>
                    <button onClick={() => setCurrentPage('job')} className={currentPage === 'job' ? 'active' : ''}>Job Analyzer</button>
                    <button onClick={() => setCurrentPage('builder')} className={currentPage === 'builder' ? 'active' : ''}>Resume Builder</button>
                    <button onClick={() => setCurrentPage('settings')} className={currentPage === 'settings' ? 'active' : ''}>Settings</button>
                </nav>
            </header>
            <main>
                {renderPage()}
            </main>
            <footer>
                <p>&copy; 2023 AI Resume Toolkit</p>
            </footer>
        </div>
    );
}

export default App;
