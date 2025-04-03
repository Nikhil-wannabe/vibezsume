import React from 'react';

const Header: React.FC = () => {
  return (
    <header>
      <h1>Vibezsume</h1>
      <nav>
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/resume-builder">Resume Builder</a></li>
          <li><a href="/contact">Contact</a></li>
        </ul>
      </nav>
    </header>
  );
};

export default Header;