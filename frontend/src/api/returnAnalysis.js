const API_BASE_URL = 'http://localhost:8000/api/v1';

// 수익률 비교 데이터 가져오기
export const fetchReturnComparison = async (symbol, startDate, endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/return-analysis/comparison`);
    url.searchParams.append('symbol', symbol);
    url.searchParams.append('start_date', startDate);
    url.searchParams.append('end_date', endDate);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.success) {
      return data.data;
    } else {
      throw new Error(data.error || 'Failed to fetch return comparison data');
    }
  } catch (error) {
    console.error('Error fetching return comparison:', error);
    throw error;
  }
};

// 수익률 분석 요약 가져오기
export const fetchReturnAnalysisSummary = async (symbol, startDate, endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/return-analysis/summary`);
    url.searchParams.append('symbol', symbol);
    url.searchParams.append('start_date', startDate);
    url.searchParams.append('end_date', endDate);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.success) {
      return data.data;
    } else {
      throw new Error(data.error || 'Failed to fetch return analysis summary');
    }
  } catch (error) {
    console.error('Error fetching return analysis summary:', error);
    throw error;
  }
};

// 수익률 분석 표 데이터 가져오기
export const fetchReturnAnalysisTable = async (symbol, startDate, endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/return-analysis/table`);
    url.searchParams.append('symbol', symbol);
    url.searchParams.append('start_date', startDate);
    url.searchParams.append('end_date', endDate);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.success) {
      return data.data;
    } else {
      throw new Error(data.error || 'Failed to fetch return analysis table');
    }
  } catch (error) {
    console.error('Error fetching return analysis table:', error);
    throw error;
  }
};

// 결합된 차트 데이터 가져오기
export const fetchCombinedReturnChart = async (symbol, startDate, endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/return-analysis/combined-chart`);
    url.searchParams.append('symbol', symbol);
    url.searchParams.append('start_date', startDate);
    url.searchParams.append('end_date', endDate);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.success) {
      return data.data;
    } else {
      throw new Error(data.error || 'Failed to fetch combined return chart data');
    }
  } catch (error) {
    console.error('Error fetching combined return chart:', error);
    throw error;
  }
};
