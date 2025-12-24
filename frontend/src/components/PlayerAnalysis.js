import React, { useState } from 'react';
import { analyzePlayer } from '../services/api';
import '../styles/PlayerAnalysis.css';

function PlayerAnalysis() {
  const [playerName, setPlayerName] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    
    if (!playerName.trim()) {
      setError('Please enter a player name');
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const result = await analyzePlayer(playerName);
      setAnalysis(result);
    } catch (err) {
      setError('Failed to analyze player. Make sure your backend is running!');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationColor = (recommendation) => {
    switch (recommendation) {
      case 'START':
        return '#22c55e';
      case 'SIT':
        return '#ef4444';
      case 'FLEX':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  const getConfidenceColor = (confidence) => {
    switch (confidence) {
      case 'HIGH':
        return '#22c55e';
      case 'MEDIUM':
        return '#f59e0b';
      case 'LOW':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  return (
    <div className="player-analysis">
      <h1>🏈 Fantasy Football AI Assistant</h1>
      
      <form onSubmit={handleAnalyze} className="search-form">
        <input
          type="text"
          placeholder="Enter player name (e.g., Patrick Mahomes)"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          className="player-input"
        />
        <button type="submit" disabled={loading} className="analyze-button">
          {loading ? 'Analyzing...' : 'Analyze Player'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {analysis && (
        <div className="analysis-result">
          <div className="player-header">
            <h2>{analysis.player_name}</h2>
            <div className="player-info">
              <span className="position">{analysis.position}</span>
              <span className="team">{analysis.team}</span>
              <span className="injury">{analysis.injury_status}</span>
            </div>
          </div>

          <div className="recommendation-card">
            <div className="recommendation-main">
              <div 
                className="recommendation-badge"
                style={{ backgroundColor: getRecommendationColor(analysis.recommendation) }}
              >
                {analysis.recommendation}
              </div>
              <div 
                className="confidence-badge"
                style={{ backgroundColor: getConfidenceColor(analysis.confidence) }}
              >
                {analysis.confidence} Confidence
              </div>
            </div>
            
            <div className="projected-points">
              <span className="points-label">Projected Points</span>
              <span className="points-value">{analysis.projected_points}</span>
            </div>
          </div>

          <div className="summary-card">
            <h3>Summary</h3>
            <p>{analysis.summary}</p>
          </div>

          <div className="factors-card">
            <h3>Key Factors</h3>
            <ul>
              {analysis.key_factors.map((factor, index) => (
                <li key={index}>{factor}</li>
              ))}
            </ul>
          </div>

          <div className="details-grid">
            <div className="detail-card upside">
              <h3>🚀 Upside</h3>
              <p>{analysis.upside}</p>
            </div>
            <div className="detail-card risks">
              <h3>⚠️ Risks</h3>
              <p>{analysis.risks}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PlayerAnalysis;