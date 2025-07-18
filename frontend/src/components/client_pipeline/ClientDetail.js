import React, { useState, useEffect } from 'react';
import { fetchClientSummary, fetchClientPerformance, fetchClientPortfolioChart } from '../../api/clients';
import PortfolioChart from './PortfolioChart';
import PortfolioAnalysis from './PortfolioAnalysis';
import PerformanceChart from './PerformanceChart';
import './ClientPipeline.css';
import './ClientDetails.css';
import titlecloud from '../../assets/titlecloud.png';
import Markdown from 'react-markdown';

const ClientDetail = ({ client, onBack, year, month, weekStr, period, inputSymbol }) => {
  const [clientData, setClientData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [portfolioChartAISummary, setPortfolioChartAISummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [performanceLoading, setPerformanceLoading] = useState(false);
  const [error, setError] = useState('');
  const [portfolioChartData, setPortfolioChartData] = useState(null);
  const [portfolioChartLoading, setPortfolioChartLoading] = useState(false);

  useEffect(() => {
    if (client && client.id) {
      loadClientSummary();
      loadPortfolioChart(client.id);
    }
    // eslint-disable-next-line
  }, [client, period]);

  // 1단계: 고객 요약 먼저 불러오기
  const loadClientSummary = async () => {
    setLoading(true);
    setError('');
    try {
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
      const summary = await fetchClientSummary(client.id, periodEndDate);
      setClientData(summary);
      setLoading(false);
      // 2단계: 성과 데이터 비동기 호출
      loadClientPerformance(client.id, periodEndDate);
    } catch (err) {
      setError('고객 상세 정보를 불러오는데 실패했습니다: ' + err.message);
      setLoading(false);
      console.error('Client detail loading error:', err);
    }
  };

  // 2단계: 성과 데이터 비동기 호출
  const loadClientPerformance = async (clientId, periodEndDate) => {
    setPerformanceLoading(true);
    try {
      const performance = await fetchClientPerformance(clientId, periodEndDate);
      setPerformanceData(performance);
    } catch (err) {
      // 성과 데이터 에러는 전체 에러로 처리하지 않음
      setPerformanceData(null);
    } finally {
      setPerformanceLoading(false);
    }
  };

  // 포트폴리오 차트 데이터 병렬 호출
  const loadPortfolioChart = async (clientId) => {
    setPortfolioChartLoading(true);
    try {
      const chartData = await fetchClientPortfolioChart(clientId);
      setPortfolioChartData(chartData);
    } catch (err) {
      setPortfolioChartData(null);
    } finally {
      setPortfolioChartLoading(false);
    }
  };

  const loadPortfolioChartAISummary = async () => {
    setPortfolioChartAISummaryLoading(true);
    try {
      const res = await fetchClientPortfolioChartAISummary(client.id);
      setPortfolioChartAISummary(res.ai_summary || '');
    } catch (e) {
      setPortfolioChartAISummary('AI 요약을 불러오지 못했습니다.');
    } finally {
      setPortfolioChartAISummaryLoading(false);
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
      <div className="industry-loading-message">
        고객 상세 정보를 불러오는 중...
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

  // periodEndDate 추출 로직 복사
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

  const { client_info, portfolio, portfolio_summary } = clientData;
  const riskProfileInfo = getRiskProfileInfo(client_info.risk_profile);

  return (
    <>
    <div className="pipeline-title">
          <img src={titlecloud} alt="cloud" />{inputSymbol} 인적사항
    </div>

      {/* 메인 콘텐츠 */}
      <div className="client-detail-content" style={{ marginLeft: '-50px', marginTop: '-50px' }}>
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
              <h4 className="client-info-item" style={{ textAlign: 'left', marginTop: '-20px' }}>특이사항</h4>
              <div className="client-memo-box" style={{ textAlign: 'left', marginTop: '-25px' }}>
                <ul className="memo-list-items">
                  {client_info.memo1 && <li className="client-info-item">{client_info.memo1}</li>}
                  {client_info.memo2 && <li className="client-info-item">{client_info.memo2}</li>}
                  {/* {client_info.memo3 && <li className="client-info-item">{client_info.memo3}</li>} */}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="pipeline-title">
          <img src={titlecloud} alt="cloud" />{inputSymbol} 수익률 한 눈에 보기
      </div>

      {/* 고객 수익률 차트 */}
      {performanceLoading ? (
        <div className="return-chart-loading">수익률 데이터를 불러오는 중...</div>
      ) : (
        <PerformanceChart 
          clientName={client_info.name}
          performanceData={performanceData}
          loading={performanceLoading}
        />
      )}

      <div style={{height:'50px' }} />

      <div className="pipeline-title">
          <img src={titlecloud} alt="cloud" />{inputSymbol} 종목 분석
      </div>

      {/* 종목 분석 */}
      <PortfolioAnalysis 
        portfolio={portfolio} 
        portfolioSummary={portfolio_summary}
        periodEndDate={periodEndDate}
      />

      <div style={{height:'50px' }} />

      <div className="pipeline-title">
          <img src={titlecloud} alt="cloud" />{inputSymbol} 진시황의 투자 분석 요약
      </div>

      {/* AI 투자 분석 요약 */}
      {performanceLoading ? (
        <div className="return-chart-loading">AI 투자 분석 요약을 불러오는 중...</div>
      ) : (
        performanceData && performanceData.ai_summary && (
          <div className="ai-summary-text">
            <Markdown>{performanceData.ai_summary}</Markdown>
          </div>
        )
      )}

      <div style={{height:'50px' }} />

      <div className="pipeline-title">
          <img src={titlecloud} alt="cloud" />{inputSymbol} 포트폴리오 분석
      </div>
      
      {/* 포트폴리오 분석 - 포트폴리오 도넛 차트 섹션 */}
      {portfolioChartLoading ? (
        <div className="return-chart-loading">포트폴리오 차트를 불러오는 중...</div>
      ) : (
        <PortfolioChart chartData={portfolioChartData} />
      )}

      {/* 페이지 말단에 back-btn 배치 */}
      <div style={{ display: 'flex', justifyContent: 'center', margin: '10px 0' }}>
        <button className="back-btn" onClick={onBack}>
          <span>←</span> 목록으로 돌아가기
        </button>
      </div>
      <div style={{height:'50px' }} />
    </>
  );
};



export default ClientDetail;
