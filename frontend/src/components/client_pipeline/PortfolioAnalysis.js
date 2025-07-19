import React from 'react';
import magnifierIcon from '../../assets/magnifier_brown.png';

const PortfolioAnalysis = ({ portfolio, portfolioSummary, periodEndDate, onStockClick }) => {
  if (!portfolio || !portfolioSummary) {
    return (
      <div className="portfolio-loading">
        <p>포트폴리오 데이터를 불러오는 중...</p>
      </div>
    );
  }

  // 종목 클릭 핸들러
  const handleStockClick = (stockName) => {
    if (onStockClick) {
      onStockClick(stockName);
    }
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
              </tr>
            </thead>
            <tbody>
              {portfolio.map((item, index) => (
                <tr key={index}>
                  <td className="stock-name" style={{ textAlign: 'center' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center', width: '100%' }}>
                      {item.stock}
                      <button 
                        className="stock-magnifier-btn"
                        onClick={() => handleStockClick(item.stock)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          padding: '2px',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                      >
                        <img 
                          src={magnifierIcon} 
                          alt="상세보기"
                          style={{ width: '16px', height: '16px' }}
                        />
                      </button>
                    </span>
                  </td>
                  <td className="stock-weight">{item.weight}%</td>
                  <td className="stock-quantity">{item.quantity.toLocaleString()}주</td>
                  <td className={`return-value ${item.weekly_return >= 0 ? 'positive' : 'negative'}`}>
                    {item.weekly_return >= 0 ? '+' : ''}{item.weekly_return}%
                  </td>
                  <td className={`return-value ${item.monthly_return >= 0 ? 'positive' : 'negative'}`}>
                    {item.monthly_return >= 0 ? '+' : ''}{item.monthly_return}%
                  </td>
                  <td className="stock-volatility">{item.volatility}%</td>
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
