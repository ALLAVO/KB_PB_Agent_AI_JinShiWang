const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const fetchAllClients = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/clients`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Clients API error:', error);
    throw error;
  }
};

export const fetchClientDetail = async (clientId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/clients/${clientId}`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Client detail API error:', error);
    throw error;
  }
};

export const fetchClientPortfolio = async (clientId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/clients/${clientId}/portfolio`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Client portfolio API error:', error);
    throw error;
  }
};

export const fetchClientSummary = async (clientId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/clients/${clientId}/summary`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Client summary API error:', error);
    throw error;
  }
};

export const fetchClientPerformance = async (clientId, periodEndDate) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/clients/${clientId}/performance/${periodEndDate}`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Client performance API error:', error);
    throw error;
  }
};
