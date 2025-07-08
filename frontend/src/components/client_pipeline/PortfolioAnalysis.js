import React from 'react';

const PortfolioAnalysis = ({ portfolio, portfolioSummary }) => {
  if (!portfolio || !portfolioSummary) {
    return (
      <div className="portfolio-analysis-section">
        <h3 className="section-title">종목 분석</h3>
        <div className="portfolio-loading">
          <p>포트폴리오 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="portfolio-analysis-section">
      <h3 className="section-title">종목 분석</h3>
      
      {/* 포트폴리오 요약 */}
      <div className="portfolio-summary">
        <div className="summary-stats">
          <div className="stat-item">
            <div className="stat-content">
              <span className="stat-label">보유 종목 수</span>
              <span className="stat-value">{portfolioSummary.total_stocks}개</span>
            </div>
          </div>
          <div className="stat-item full-width">
            <div className="stat-content">
              <span className="stat-label">총 보유 수량</span>
              <span className="stat-value">{portfolioSummary.total_quantity.toLocaleString()}주</span>
            </div>
          </div>
          <div className="stat-item full-width">
            <div className="stat-content">
              <span className="stat-label">투자 섹터</span>
              <div className="sectors-container">
                {portfolioSummary.sectors.map((sector, index) => (
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
    </div>
  );
};

export default PortfolioAnalysis;
