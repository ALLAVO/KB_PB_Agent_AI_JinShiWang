import React, { useState, useEffect } from 'react';
import { fetchClientSummary, fetchClientPerformance } from '../../api/clients';
import PortfolioChart from './PortfolioChart';
import PortfolioAnalysis from './PortfolioAnalysis';
import PerformanceChart from './PerformanceChart';
import './ClientPipeline.css';
import './ClientDetails.css';
import titlecloud from '../../assets/titlecloud.png';

const ClientDetail = ({ client, onBack, year, month, weekStr, period }) => {
  const [clientData, setClientData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (client && client.id) {
      loadClientDetail();
    }
  }, [client, period]);

  const loadClientDetail = async () => {
    setLoading(true);
    setError('');
    try {
      // period에서 종료일 추출 - null/undefined 체크 추가
      let periodEndDate;
      if (period && typeof period === 'string') {
        const dateMatch = period.match(/(\d{2})\.(\d{2}) - (\d{2})\.(\d{2})/);
        if (dateMatch) {
          periodEndDate = `${year}-${dateMatch[3]}-${dateMatch[4]}`;
        } else {
          periodEndDate = new Date().toISOString().split('T')[0];
        }
      } else {
        periodEndDate = new Date().toISOString().split('T')[0];
      }

      const [summary, performance] = await Promise.all([
        fetchClientSummary(client.id, periodEndDate),
        fetchClientPerformance(client.id, periodEndDate)
      ]);
      
      setClientData(summary);
      setPerformanceData(performance);
    } catch (err) {
      setError('고객 상세 정보를 불러오는데 실패했습니다: ' + err.message);
      console.error('Client detail loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount) => {
    if (amount >= 100000000) {
      return `${(amount / 100000000).toFixed(1)}억원`;
    } else if (amount >= 10000) {
      return `${(amount / 10000).toFixed(0)}만원`;
    }
    return `${amount.toLocaleString()}원`;
  };

  const getRiskProfileInfo = (riskProfile) => {
    const profiles = {
      'Conservative': { label: '안정형', description: '안정적인 수익을 추구하는 투자성향', color: '#7BA05B' },
      'Moderate': { label: '중립형', description: '적절한 위험을 감수하는 투자성향', color: '#D4B96A' },
      'Aggressive': { label: '적극형', description: '높은 수익을 위해 위험을 감수하는 투자성향', color: '#C4756E' },
      'Very Conservative': { label: '매우안정형', description: '위험을 최소화하는 투자성향', color: '#8B7355' },
      'Very Aggressive': { label: '매우적극형', description: '최고 수익을 위해 높은 위험을 감수하는 투자성향', color: '#6D5A42' }
    };
    return profiles[riskProfile] || { label: riskProfile, description: '', color: '#666' };
  };

  const getClientImage = (clientName) => {
    try {
      return require(`../../assets/client_profile/${clientName}.png`);
    } catch (error) {
      return require('../../assets/client_profile/default.png');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px 0', textAlign: 'center', background: 'transparent', border: 'none' }}>
        <span>고객 상세 정보를 불러오는 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="client-detail-error">
        <h3>오류가 발생했습니다</h3>
        <p>{error}</p>
        <button className="back-btn" onClick={onBack}>목록으로 돌아가기</button>
      </div>
    );
  }

  if (!clientData) {
    return <div>고객 정보를 불러오고 있습니다...</div>;
  }

  const { client_info, portfolio, portfolio_summary } = clientData;
  const riskProfileInfo = getRiskProfileInfo(client_info.risk_profile);

  return (
    <>
      {/* 메인 콘텐츠 */}
      <div className="client-detail-content" style={{ maxWidth: '2000px', margin: '0 auto' }}>
        {/* 좌측: 고객 이미지 */}
        <div className="client-image-section">
          <div className="client-profile-image">
            <img 
              src={getClientImage(client_info.name)}
              alt={client_info.name}
              onError={(e) => {
                try {
                  e.target.src = require('../../assets/client_profile/default.png');
                } catch (error) {
                  // fallback: 기본 아바타 또는 빈 이미지
                  e.target.style.display = 'none';
                }
              }}
            />
          </div>
        </div>

        {/* 우측: 고객 정보 */}
        <div className="client-info-section">
          <div className="client-info-header">
            <div className="client-info-row">
              <span className="client-info-item">
                <strong>성함</strong> {client_info.name}
              </span>
              <span className="client-info-item">
                <strong>성별/나이</strong> {client_info.sex}/{client_info.age}세
              </span>
              <span className="client-info-item">
                <strong>투자기간</strong> 30년
              </span>
            </div>
            <div className="client-info-row">
              <span className="client-info-item">
                <strong>위험 성향</strong> 위험 중립형
              </span>
              <span className="client-info-item">
                <strong>주식 투자금액</strong> {formatAmount(client_info.total_amount)}
              </span>
            </div>
          </div>
          
          {/* 특이사항 박스 */}
          {(client_info.memo1 || client_info.memo2 || client_info.memo3) && (
            <>
              <div style={{ textAlign: 'left', marginTop: '-17px' }}>
                <span className="client-info-item" style={{ fontWeight: 'bold', color: '#302A24', fontSize: '18px' }}>특이사항</span>
              </div>
              <div className="client-memo-box" style={{ marginTop: '-10px' }}>
                <ul className="memo-list-items">
                  {client_info.memo1 && <li>{client_info.memo1}</li>}
                  {client_info.memo2 && <li>{client_info.memo2}</li>}
                  {/* {client_info.memo3 && <li>{client_info.memo3}</li>} */}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
      <div className="pipeline-title">
        <img src={titlecloud} alt="cloud" /> {'AI 투자 분석 요약'}
      </div>
      {performanceData && performanceData.ai_summary && (
        <div style={{ background: '#ede8dd', borderRadius: '18px', padding: '20px 32px', marginBottom: '10px', maxWidth: '750px', marginLeft: 'auto', marginRight: 'auto' }}>
          <p className="ai-summary-text" style={{ background: 'none', borderLeft: 'none', padding: 0, margin: 0, fontSize: '1.0rem', color: '#302A24', textAlign: 'left', lineHeight: 1.5 }}>
            {performanceData.ai_summary && performanceData.ai_summary
              .replace(/(1\.|2\.|3\.)/g, '\n$1')
              .split(/\n(.+?\.)/).map((part, idx, arr) => {
                if (part === '' || part === undefined) return null;
                // Only add <br /> before 1., 2., 3. (not after)
                if (/^(1\.|2\.|3\.)/.test(part) && idx !== 0) {
                  return <React.Fragment key={idx}><br />{part}</React.Fragment>;
                }
                return <React.Fragment key={idx}>{part}</React.Fragment>;
              })}
          </p>
        </div>
      )}

      {/* 고객 수익률 차트 */}
      <PerformanceChart 
        clientName={client_info.name}
        performanceData={performanceData}
        loading={loading}
      />

      {/* 종목 분석 */}
      <PortfolioAnalysis 
        portfolio={portfolio} 
        portfolioSummary={portfolio_summary} 
      />
      
      {/* 포트폴리오 분석 - 포트폴리오 도넛 차트 섹션 */}
      <PortfolioChart clientId={client.id} 
      />

      {/* 페이지 말단에 back-btn 배치 */}
      <div style={{ display: 'flex', justifyContent: 'center', margin: '32px 0' }}>
        <button className="back-btn" onClick={onBack}>
          <span>←</span> 목록으로 돌아가기
        </button>
      </div>
    </>
  );
};



export default ClientDetail;
