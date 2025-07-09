import React, { useState, useEffect } from 'react';

function CompanyInfo({ symbol }) {
  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!symbol) return;

    const fetchCompanyInfo = async () => {
      setLoading(true);
      setError("");
      
      try {
        const response = await fetch(`/api/v1/companies/${symbol}/info`);
        if (!response.ok) {
          throw new Error('기업 정보를 불러오는데 실패했습니다.');
        }
        const data = await response.json();
        setCompanyData(data);
      } catch (e) {
        console.error('기업 정보 조회 오류:', e);
        setError(e.message || '데이터를 불러오지 못했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchCompanyInfo();
  }, [symbol]);

  if (loading) {
    return (
      <div style={{ 
        background: '#fff', 
        padding: '20px', 
        borderRadius: '8px', 
        marginBottom: '20px' 
      }}>
        <p>기업 정보를 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        background: '#fff', 
        padding: '20px', 
        borderRadius: '8px', 
        marginBottom: '20px',
        color: 'red'
      }}>
        <p>오류: {error}</p>
      </div>
    );
  }

  if (!companyData) {
    return null;
  }

  return (
    <div style={{ width: '100%' }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: '0.8fr 1.2fr', // 기업 정보:사업 개요 비율 조정
        gap: '32px',
        alignItems: 'flex-start',
        width: '100%'
      }}>
        {/* 좌측: 기업 정보 */}
        <div style={{ minWidth: 0, textAlign: 'left', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', maxWidth: '350px' }}>
          <div style={{ fontSize: '1.0rem', color: '#302A24', marginLeft: '20px', marginBottom: '18px', lineHeight: 1.5, textAlign: 'left', display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
            <div><strong>기업명:</strong> {companyData.company_name || '정보 없음'}</div>
            {/* <div><strong>종목코드:</strong> {companyData.stock_symbol || '정보 없음'}</div> */}
            <div><strong>산업:</strong> {companyData.industry || '정보 없음'}</div>
            <div><strong>섹터:</strong> {companyData.sector || '정보 없음'}</div>
            <div><strong>주소:</strong> {companyData.address || '정보 없음'}</div>
          </div>
        </div>
        {/* 우측: 사업 개요 */}
        <div style={{ minWidth: 0, textAlign: 'left', fontSize: '1.0rem', color: '#302A24', lineHeight: 1.5 }}>
          <strong>사업 개요:</strong>
          <div style={{ marginTop: '12px', whiteSpace: 'pre-line', textAlign: 'left' }}>
            {companyData.business_summary || '정보 없음'}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CompanyInfo;
