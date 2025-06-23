// sentiment.js - 감성 분석 관련 API 호출 함수

/**
 * 주차별 감성점수 조회 API 호출
 * @param {string} stockSymbol
 * @param {string} startDate (YYYY-MM-DD)
 * @param {string} endDate (YYYY-MM-DD)
 * @returns {Promise<object>}
 */
export async function fetchWeeklySentiment(stockSymbol, startDate, endDate) {
  const params = new URLSearchParams({
    stock_symbol: stockSymbol,
    start_date: startDate,
    end_date: endDate
  });
  const response = await fetch(`http://localhost:8000/api/v1/sentiment/weekly?${params.toString()}`);
  if (!response.ok) throw new Error('감성점수 API 호출 실패');
  return await response.json();
}


