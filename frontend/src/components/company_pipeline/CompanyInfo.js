import React from 'react';

// 인라인 스타일 정의
const sectorLinkStyle = {
  marginLeft: '8px',
  color: '#6D5A42',
  cursor: 'pointer',
  textDecoration: 'underline',
  fontSize: '12px',
  fontWeight: 'normal',
  transition: 'color 0.2s ease'
};

function CompanyInfo({ companyData, loading, error, onIndustryClick, companySector }) {
  // DB에서 가져온 섹터 정보 우선 사용
  const sectorInfo = companySector?.sector || companyData?.sector || null;
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
            <div>
              <strong>섹터:</strong> {sectorInfo || '정보 없음'}
              {sectorInfo && sectorInfo !== '정보 없음' && onIndustryClick && (
                <span 
                  onClick={() => onIndustryClick(sectorInfo)}
                  style={sectorLinkStyle}
                  title={`${sectorInfo} 산업 분석으로 이동`}
                  onMouseEnter={(e) => {
                    e.target.style.color = '#8B7355';
                    e.target.style.textDecoration = 'underline';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.color = '#6D5A42';
                    e.target.style.textDecoration = 'underline';
                  }}
                >
                  (더 알아보기)
                </span>
              )}
            </div>
            <div><strong>산업:</strong> {companyData.industry || '정보 없음'}</div>
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
