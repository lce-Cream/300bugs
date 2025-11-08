
import React from 'react';
import './minimalist-theme.css';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ChatWithBot from './pages/ChatWithBot';
import FAQ from './pages/FAQ';
import ArchiveUpload from './pages/ArchiveUpload';
import PredictiveAccounting from './pages/PredictiveAccounting';

const App: React.FC = () => (
  <Router>
    <nav style={{ display: 'flex', gap: 20, margin: 20 }}>
      <Link to="/">Home</Link>
      <Link to="/chat">Chat with Bot</Link>
      <Link to="/faq">FAQ</Link>
      <Link to="/archive-upload">Archive Upload</Link>
      <Link to="/predictive-accounting">Predictive Accounting</Link>
    </nav>
    <div className="center-wrapper">
      <Routes>
        <Route path="/" element={<div style={{textAlign:'center'}}><h1>Welcome to the App</h1></div>} />
        <Route path="/chat" element={<ChatWithBot />} />
        <Route path="/faq" element={<FAQ />} />
        <Route path="/archive-upload" element={<ArchiveUpload />} />
        <Route path="/predictive-accounting" element={<PredictiveAccounting />} />
      </Routes>
    </div>
  </Router>
);

export default App;
