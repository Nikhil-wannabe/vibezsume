import React from 'react';
import Header from './components/Header';

const App: React.FC = () => {
  return (
    <div>
      <Header />
      <main>
        <h2>Welcome to Vibezsume</h2>
        <p>Start building your perfect resume today!</p>
      </main>
    </div>
  );
};

export default App;