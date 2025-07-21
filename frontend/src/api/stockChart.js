const API_BASE_URL = 'http://localhost:8000/api/v1';

// 조합된 차트 데이터 가져오기 (주가, 이동평균, 거래량 조합)
export const fetchCombinedStockChart = async (symbol, startDate, endDate, chartTypes = ['price'], maPeriods = [5, 20, 60]) => {
  try {
    const chartTypesStr = chartTypes.join(',');
    const maPeriodsStr = maPeriods.join(',');
    
    const url = new URL(`${API_BASE_URL}/stock-chart/combined-chart`);
    url.searchParams.append('symbol', symbol);
    url.searchParams.append('start_date', startDate);
    url.searchParams.append('end_date', endDate);
    url.searchParams.append('chart_types', chartTypesStr);
    url.searchParams.append('ma_periods', maPeriodsStr);

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
      throw new Error(data.error || 'Failed to fetch combined stock chart data');
    }
  } catch (error) {
    console.error('Error fetching combined stock chart:', error);
    throw error;
  }
};

// 주가 차트 요약 정보 가져오기
export const fetchStockChartSummary = async (symbol, startDate, endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/stock-chart/summary`);
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
      throw new Error(data.error || 'Failed to fetch stock chart summary');
    }
  } catch (error) {
    console.error('Error fetching stock chart summary:', error);
    throw error;
  }
};

// 상세 주식 정보 가져오기
export const fetchEnhancedStockInfo = async (symbol) => {
  try {
    const url = new URL(`${API_BASE_URL}/companies/${symbol}/enhanced-info`);

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
      throw new Error(data.error || 'Failed to fetch enhanced stock info');
    }
  } catch (error) {
    console.error('Error fetching enhanced stock info:', error);
    throw error;
  }
};
