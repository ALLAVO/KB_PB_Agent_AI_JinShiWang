const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export async function fetchIndustryTop3Articles({ sector, startDate }) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/industry/top3_articles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sector: sector,
        start_date: startDate
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching industry top3 articles:', error);
    throw error;
  }
}
