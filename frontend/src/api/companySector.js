/**
 * 기업 섹터 정보 API
 */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * 기업의 티커로 섹터 정보를 조회
 * @param {string} ticker - 기업 티커 심볼
 * @returns {Promise<Object>} 섹터 정보
 */
export const fetchCompanySector = async (ticker) => {
  try {
    const response = await fetch(`${API_BASE_URL}/companies/${ticker}/sector`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.status === 'success') {
      return data.data;
    } else {
      throw new Error(data.message || '섹터 정보를 가져오는데 실패했습니다.');
    }
  } catch (error) {
    console.error('Error fetching company sector:', error);
    throw error;
  }
};
