import React, { useState, useEffect } from 'react';
import { fetchClientSummary, fetchClientPerformance } from '../../api/clients';
import PortfolioChart from './PortfolioChart';
import PortfolioAnalysis from './PortfolioAnalysis';
import PerformanceChart from './PerformanceChart';
import './ClientPipeline.css';

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
      <div className="client-detail-loading">
        <div className="loading-spinner"></div>
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
    <div className="client-detail-container">
      {/* 헤더 */}
      <div className="client-detail-header">
        <button className="back-btn" onClick={onBack}>
          <span>←</span> 목록으로 돌아가기
        </button>
        <h1 className="client-detail-title">
          {client_info.name}님 분석 포트폴리오
        </h1>
        <div className="period-info">{year}년 {month}월 {weekStr}</div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="client-detail-content">
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
          <div className="client-basic-info-panel">
            <h3 className="info-panel-title">기본 정보</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">성명:</span>
                <span className="info-value">{client_info.name}</span>
              </div>
              <div className="info-item">
                <span className="info-label">성별:</span>
                <span className="info-value">{client_info.sex}</span>
              </div>
              <div className="info-item">
                <span className="info-label">나이:</span>
                <span className="info-value">{client_info.age}세</span>
              </div>
              <div className="info-item">
                <span className="info-label">위험성향:</span>
                <span className="info-value risk-profile" style={{color: riskProfileInfo.color}}>
                  {riskProfileInfo.label}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">투자기간:</span>
                <span className="info-value">{client_info.investment_horizon}</span>
              </div>
              <div className="info-item total-amount-item">
                <span className="info-label">총 투자금액:</span>
                <span className="info-value total-amount">{formatAmount(client_info.total_amount)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 메모 정보 - 전체 너비 */}
      {(client_info.memo1 || client_info.memo2 || client_info.memo3) && (
        <div className="client-memo-section">
          <div className="memo-list">
            {client_info.memo1 && (
              <div className="memo-item">
                <div className="memo-content">{client_info.memo1}</div>
              </div>
            )}
            {client_info.memo2 && (
              <div className="memo-item">
                <div className="memo-content">{client_info.memo2}</div>
              </div>
            )}
            {client_info.memo3 && (
              <div className="memo-item">
                <div className="memo-content">{client_info.memo3}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI 투자 분석 요약 */}
      {performanceData && performanceData.ai_summary && (
        <div className="ai-analysis-section">
          <h3 className="section-title">AI 투자 분석 요약</h3>
          <div className="ai-analysis-content-combined">
            <div className="ai-combined-card">
              <div className="ai-summary-section">
                <h4 className="ai-section-title">투자 성과 분석</h4>
                <p className="ai-summary-text">{performanceData.ai_summary}</p>
              </div>
            </div>
          </div>
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
    </div>
  );
};



export default ClientDetail;
