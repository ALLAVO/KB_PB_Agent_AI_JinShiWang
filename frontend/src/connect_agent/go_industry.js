import { fetchIndustryTop3Articles, fetchIndustryTop10Companies } from '../api/industry';

// 산업 agent 분석 실행 함수
export async function goToIndustryAgent(sector, endDate, onResult) {
  try {
    // 산업 기사 및 기업 데이터 fetch
    const articles = await fetchIndustryTop3Articles({ sector, endDate });
    const companies = await fetchIndustryTop10Companies({ sector, endDate });
    // 결과 콜백 (예: 페이지 이동, 데이터 전달 등)
    if (onResult) {
      onResult({ sector, endDate, articles, companies });
    }
    // 필요시 라우팅 추가
    // 예: window.location.href = `/industry-agent?sector=${sector}&endDate=${endDate}`;
  } catch (error) {
    console.error('산업 agent 분석 오류:', error);
  }
}
