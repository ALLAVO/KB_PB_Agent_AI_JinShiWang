// 기업 심볼, 시작일, 종료일을 받아 백엔드로부터 주가 예측 데이터를 받아오는 함수

export async function fetchPredictionSummary({ symbol, startDate, endDate }) {
  const url = `/api/v1/prediction/summary`;

  const requestBody = {
    stock_symbol: symbol,
    start_date: startDate,
    end_date: endDate
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      },
      body: JSON.stringify(requestBody),
      cache: "no-store"
    });
    
    if (!response.ok) {
      throw new Error('서버 응답 오류');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('주가 예측 fetch 실패:', error);
    throw error;
  }
}
