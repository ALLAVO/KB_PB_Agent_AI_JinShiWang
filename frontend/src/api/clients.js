const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const fetchAllClients = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/clients`);
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
    const response = await fetch(`${API_BASE_URL}/clients/${clientId}`);
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
    const response = await fetch(`${API_BASE_URL}/clients/${clientId}/portfolio`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Client portfolio API error:', error);
    throw error;
  }
};

export const fetchClientSummary = async (clientId, periodEndDate = null) => {
  try {
    let url = `${API_BASE_URL}/clients/${clientId}/summary`;
    if (periodEndDate) {
      url += `?period_end_date=${periodEndDate}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching client summary:', error);
    throw error;
  }
};

export const fetchClientPerformance = async (clientId, periodEndDate) => {
  try {
    const response = await fetch(`${API_BASE_URL}/clients/${clientId}/performance/${periodEndDate}`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Client performance API error:', error);
    throw error;
  }
};

export const fetchClientPortfolioChart = async (clientId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/clients/${clientId}/portfolio-chart`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Client portfolio chart API error:', error);
    throw error;
  }
};
