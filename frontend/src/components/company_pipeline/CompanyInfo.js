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
      <div style={{ display: 'flex', alignItems: 'flex-start', width: '100%' }}>
        {/* 좌측: 로고(네모) */}
        <div style={{
          minWidth: '260px',
          minHeight: '180px',
          maxWidth: '320px',
          maxHeight: '220px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#f3f3f3',
          borderRadius: '12px',
          boxShadow: '0 1px 4px #0001',
          fontSize: '2.8rem',
          fontWeight: 'bold',
          color: '#222',
          marginRight: '32px',
          flex: 'none',
          textAlign: 'left'
        }}>
          {/* 실제 로고가 있다면 <img src={companyData.logo_url} ... /> */}
          <span style={{fontSize: '2.6rem', fontWeight: 700, letterSpacing: '-0.04em', textAlign: 'left'}}>LOGO</span>
        </div>
        {/* 우측: 기업 정보 */}
        <div style={{ flex: 1, minWidth: 0, textAlign: 'left', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start' }}>
          <div style={{ fontSize: '1.15rem', color: '#111', marginBottom: '18px', lineHeight: 1.7, textAlign: 'left', display: 'flex', flexWrap: 'wrap', gap: '32px' }}>
            <div><strong>기업명:</strong> {companyData.company_name || '정보 없음'}</div>
            <div><strong>종목코드:</strong> {companyData.stock_symbol || '정보 없음'}</div>
            <div><strong>산업:</strong> {companyData.industry || '정보 없음'}</div>
            <div><strong>섹터:</strong> {companyData.sector || '정보 없음'}</div>
            <div><strong>주소:</strong> {companyData.address || '정보 없음'}</div>
          </div>
        </div>
      </div>
      {/* 아래쪽: 사업 개요 */}
      {companyData.business_summary && (
        <div style={{ fontSize: '1.1rem', color: '#222', marginTop: '15px', marginBottom: '12px', lineHeight: 1.2, textAlign: 'left' }}>
          <strong>사업 개요:</strong>
          <div style={{ marginTop: '12px', whiteSpace: 'pre-line', textAlign: 'left' }}>{companyData.business_summary}</div>
        </div>
      )}
    </div>
  );
}

export default CompanyInfo;
