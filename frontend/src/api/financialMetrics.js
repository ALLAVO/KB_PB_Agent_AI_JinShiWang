export const fetchFinancialMetrics = async ({ symbol, endDate }) => {
  const params = new URLSearchParams();
  if (endDate) params.append('end_date', endDate);

  const url = `/api/v1/financial-metrics/${symbol}${params.toString() ? `?${params.toString()}` : ''}`;

  try {
    const response = await fetch(url, { 
      cache: "no-store",
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching financial metrics:', error);
    throw error;
  }
};
