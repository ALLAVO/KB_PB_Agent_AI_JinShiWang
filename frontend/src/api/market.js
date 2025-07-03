const API_BASE_URL = 'http://localhost:8000/api/v1';

// 미국 주요 지수 6개월치 데이터 가져오기
export const fetchIndices6MonthsChart = async (endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/market/indices-6months-chart`);
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
    return data;
  } catch (error) {
    console.error('Error fetching indices chart data:', error);
    throw error;
  }
};

// 미국 국채 금리 6개월치 데이터 가져오기
export const fetchTreasuryYields6MonthsChart = async (endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/market/treasury-yields-6months-chart`);
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
    return data;
  } catch (error) {
    console.error('Error fetching treasury yields chart data:', error);
    throw error;
  }
};

// 환율 6개월치 데이터 가져오기
export const fetchFx6MonthsChart = async (endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/market/fx-6months-chart`);
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
    return data;
  } catch (error) {
    console.error('Error fetching FX chart data:', error);
    throw error;
  }
};

// 미국 주요 지수 1년치 데이터 가져오기 (테이블용)
export const fetchIndices1YearChart = async (endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/market/indices-1year-chart`);
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
    return data;
  } catch (error) {
    console.error('Error fetching 1-year indices data:', error);
    throw error;
  }
};

// 미국 국채 금리 1년치 데이터 가져오기
export const fetchTreasuryYields1YearChart = async (endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/market/treasury-yields-1year-chart`);
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
    return data;
  } catch (error) {
    console.error('Error fetching 1-year treasury yields data:', error);
    throw error;
  }
};

// 환율 1년치 데이터 가져오기
export const fetchFx1YearChart = async (endDate) => {
  try {
    const url = new URL(`${API_BASE_URL}/market/fx-1year-chart`);
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
    return data;
  } catch (error) {
    console.error('Error fetching 1-year FX data:', error);
    throw error;
  }
};
