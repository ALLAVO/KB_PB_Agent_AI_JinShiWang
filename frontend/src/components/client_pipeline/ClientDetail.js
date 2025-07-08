import React, { useState, useEffect } from 'react';
import { fetchClientSummary, fetchClientPerformance } from '../../api/clients';
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
        fetchClientSummary(client.id),
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
      <div className="weekly-summary-section">
        <h3 className="section-title">{client_info.name} 고객님 수익률 차트</h3>
        <div className="summary-content">
          {performanceData ? (
            <div className="performance-analysis">
              <div className="performance-summary">
                <div className="performance-info">
                  <span className="performance-label">분석 기준일:</span>
                  <span className="performance-value">{performanceData.period_end}</span>
                </div>
                <div className="performance-info">
                  <span className="performance-label">벤치마크:</span>
                  <span className="performance-value">
                    {performanceData.benchmark}
                    {performanceData.benchmark_symbol && (
                      <span className="benchmark-symbol"> ({performanceData.benchmark_symbol})</span>
                    )}
                  </span>
                </div>
                <div className="performance-info">
                  <span className="performance-label">성과구간:</span>
                  <span className="performance-value">{performanceData.performance_period_months}개월</span>
                </div>
              </div>
              
              <div className="performance-table-container">
                <table className="performance-table">
                  <thead>
                    <tr>
                      <th>구분</th>
                      <th>포트폴리오 수익률</th>
                      <th>벤치마크 수익률<br/>
                        <small style={{fontWeight: 'normal', opacity: 0.8}}>
                          ({performanceData.benchmark})
                        </small>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="period-label">일주일간 수익률</td>
                      <td className={`return-value ${performanceData.weekly_return.portfolio >= 0 ? 'positive' : 'negative'}`}>
                        {performanceData.weekly_return.portfolio >= 0 ? '+' : ''}{performanceData.weekly_return.portfolio}%
                      </td>
                      <td className={`return-value ${performanceData.weekly_return.benchmark >= 0 ? 'positive' : 'negative'}`}>
                        {performanceData.weekly_return.benchmark >= 0 ? '+' : ''}{performanceData.weekly_return.benchmark}%
                      </td>
                    </tr>
                    <tr>
                      <td className="period-label">성과구간 수익률 ({performanceData.performance_period_months}개월)</td>
                      <td className={`return-value ${performanceData.performance_return.portfolio >= 0 ? 'positive' : 'negative'}`}>
                        {performanceData.performance_return.portfolio >= 0 ? '+' : ''}{performanceData.performance_return.portfolio}%
                      </td>
                      <td className={`return-value ${performanceData.performance_return.benchmark >= 0 ? 'positive' : 'negative'}`}>
                        {performanceData.performance_return.benchmark >= 0 ? '+' : ''}{performanceData.performance_return.benchmark}%
                      </td>
                    </tr>
                  </tbody>
                </table>
                <small className="coming-soon">* 성과 구간은 고객님 최근 리밸런싱 이후부터 지난주 금요일까지를 대상으로 합니다.</small>
              </div>
            </div>
          ) : loading ? (
            <div className="summary-placeholder">
              <p>수익률 데이터를 불러오는 중...</p>
            </div>
          ) : (
            <div className="summary-placeholder">
              <p>수익률 데이터를 불러올 수 없습니다.</p>
            </div>
          )}
        </div>
      </div>

      {/* 종목 분석 */}
      <div className="portfolio-analysis-section">
        <h3 className="section-title">종목 분석</h3>
        
        {/* 포트폴리오 요약 */}
        <div className="portfolio-summary">
          <div className="summary-stats">
            <div className="stat-item">
              <div className="stat-content">
                <span className="stat-label">보유 종목 수</span>
                <span className="stat-value">{portfolio_summary.total_stocks}개</span>
              </div>
            </div>
            <div className="stat-item full-width">
              <div className="stat-content">
                <span className="stat-label">총 보유 수량</span>
                <span className="stat-value">{portfolio_summary.total_quantity.toLocaleString()}주</span>
              </div>
            </div>
            <div className="stat-item full-width">
              <div className="stat-content">
                <span className="stat-label">투자 섹터</span>
                <div className="sectors-container">
                  {portfolio_summary.sectors.map((sector, index) => (
                    <span key={index} className="sector-item">{sector}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 포트폴리오 테이블 */}
        {portfolio.length > 0 ? (
          <div className="portfolio-table-container">
            <table className="portfolio-table">
              <thead>
                <tr>
                  <th>종목명</th>
                  <th>보유 수량</th>
                  <th>섹터</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.map((item, index) => (
                  <tr key={index}>
                    <td className="stock-name">{item.stock}</td>
                    <td className="stock-quantity">{item.quantity.toLocaleString()}주</td>
                    <td className="stock-sector">
                      <span className="sector-badge">{item.sector}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="no-portfolio-message">
            <p>보유 중인 종목이 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClientDetail;
