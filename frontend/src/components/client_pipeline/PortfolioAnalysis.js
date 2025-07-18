import React from 'react';
import { goToIndustryAgent } from '../../connect_agent/go_industry';

const PortfolioAnalysis = ({ portfolio, portfolioSummary, periodEndDate }) => {
  if (!portfolio || !portfolioSummary) {
    return (
      <div className="portfolio-loading">
        <p>포트폴리오 데이터를 불러오는 중...</p>
      </div>
    );
  }

  // 산업 agent 버튼 클릭 핸들러
  const handleSectorButtonClick = (sector) => {
    if (!periodEndDate) return;
    goToIndustryAgent(sector, periodEndDate, (result) => {
      // 예시: 결과 처리 또는 페이지 이동
      // window.location.href = `/industry-agent?sector=${sector}&endDate=${periodEndDate}`;
      // 또는 결과를 상위 컴포넌트로 전달
      console.log('산업 agent 분석 결과:', result);
    });
  };

  return (
    <>
      {/* 포트폴리오 테이블 */}
      {portfolio.length > 0 ? (
        <div className="portfolio-table-container" style={{ marginLeft: '40px', width: '800px' }}>
          <table className="portfolio-table">
            <thead>
              <tr>
                <th>종목명</th>
                <th>비중</th>
                <th>보유 수량</th>
                <th>1주일 수익률</th>
                <th>1달 수익률</th>
                <th>변동성</th>
                <th>섹터</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map((item, index) => (
                <tr key={index}>
                  <td className="stock-name">{item.stock}</td>
                  <td className="stock-weight">{item.weight}%</td>
                  <td className="stock-quantity">{item.quantity.toLocaleString()}주</td>
                  <td className={`return-value ${item.weekly_return >= 0 ? 'positive' : 'negative'}`}>
                    {item.weekly_return >= 0 ? '+' : ''}{item.weekly_return}%
                  </td>
                  <td className={`return-value ${item.monthly_return >= 0 ? 'positive' : 'negative'}`}>
                    {item.monthly_return >= 0 ? '+' : ''}{item.monthly_return}%
                  </td>
                  <td className="stock-volatility">{item.volatility}%</td>
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
    </>
  );
};

export default PortfolioAnalysis;
