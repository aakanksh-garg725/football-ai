import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const analyzePlayer = async (playerName, includeStats = true, includeMatchup = false) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/players/analyze`, {
      player_name: playerName,
      include_stats: includeStats,
      include_matchup: includeMatchup
    });
    return response.data;
  } catch (error) {
    console.error('Error analyzing player:', error);
    throw error;
  }
};

export const searchPlayer = async (playerName) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/players/search/${playerName}`);
    return response.data;
  } catch (error) {
    console.error('Error searching player:', error);
    throw error;
  }
};

export const comparePlayers = async (playerNames) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/players/compare`, {
      player_names: playerNames
    });
    return response.data;
  } catch (error) {
    console.error('Error comparing players:', error);
    throw error;
  }
};