import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import './App.css';
import Auth from './components/Auth/Auth';
import Hangar from './components/Hangar/Hangar';
import BattleCanvas from './components/Game/BattleCanvas'

const App: React.FC = () => {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Auth />} />
                <Route path="/hangar" element={<Hangar />} />
                <Route path="/" element={<Navigate to="/login" />} />
                <Route path="/battle/:battleId" element={<BattleCanvas />} />
            </Routes>
        </Router>
    );
};

export default App;