// 기업 심볼, 시작일, 종료일을 받아 백엔드로부터 주차별 감성점수 데이터를 받아오는 함수

export async function fetchWeeklySentiment({ symbol, startDate, endDate }) {
  const params = new URLSearchParams();
  params.append('stock_symbol', symbol);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const url = `/api/v1/sentiment/weekly?${params.toString()}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('서버 응답 오류');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('감성 점수 fetch 실패:', error);
    throw error;
  }
}

