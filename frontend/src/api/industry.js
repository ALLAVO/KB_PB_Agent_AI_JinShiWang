// proxy 설정 때문에 상대 경로 사용
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export async function fetchIndustryTop3Articles({ sector, startDate }) {
  try {
    const url = `${API_BASE_URL}/industry/top3_articles`;
    console.log('🔗 API 요청 URL:', url);
    console.log('📊 요청 데이터:', { sector, startDate });
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sector: sector,
        start_date: startDate
      }),
    });

    console.log('📡 응답 상태:', response.status, response.statusText);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ 응답 데이터:', data);
    return data;
  } catch (error) {
    console.error('❌ Error fetching industry top3 articles:', error);
    throw error;
  }
}

export async function fetchIndustryTop10Companies({ sector, endDate }) {
  try {
    const url = `${API_BASE_URL}/industry/top10_companies`;
    console.log('🔗 API 요청 URL:', url);
    console.log('📊 요청 데이터:', { sector, endDate });
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sector: sector,
        end_date: endDate
      }),
    });

    console.log('📡 응답 상태:', response.status, response.statusText);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ 응답 데이터:', data);
    return data;
  } catch (error) {
    console.error('❌ Error fetching industry top10 companies:', error);
    throw error;
  }
}
