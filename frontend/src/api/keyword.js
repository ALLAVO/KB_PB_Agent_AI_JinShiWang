// 기업 심볼, 시작일, 종료일을 받아 백엔드로부터 키워드 데이터를 받아오는 함수

export async function fetchWeeklyKeywords({ symbol, startDate, endDate }) {
  const params = new URLSearchParams();
  params.append('stock_symbol', symbol);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const url = `/api/v1/keyword/weekly?${params.toString()}`;

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
      throw new Error('서버 응답 오류');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('키워드 fetch 실패:', error);
    throw error;
  }
}
