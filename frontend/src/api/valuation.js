export const fetchValuationMetrics = async ({ symbol, endDate }) => {
  try {
    let url = `/api/v1/valuation?symbol=${encodeURIComponent(symbol)}`;
    
    if (endDate) {
      url += `&end_date=${encodeURIComponent(endDate)}`;
    }
    
    console.log('벨류에이션 지표 요청 URL:', url);
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('벨류에이션 지표 응답:', data);
    
    return data;
  } catch (error) {
    console.error('벨류에이션 지표 조회 실패:', error);
    throw error;
  }
};
