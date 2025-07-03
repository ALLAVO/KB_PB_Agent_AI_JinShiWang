const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const fetchCompanyProfile = async (symbol) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/company-profile/${symbol}`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Company profile API error:', error);
    throw error;
  }
};

export const fetchCompanyFinancialAnalysis = async (symbol, startDate = null, endDate = null) => {
  try {
    let url = `${API_BASE_URL}/api/v1/companies/${symbol}/financial-analysis`;
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Company financial analysis API error:', error);
    throw error;
  }
};
