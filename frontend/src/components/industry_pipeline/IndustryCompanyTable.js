import React from 'react';
import './IndustryCompanyTable.css';
import magnifierIcon from '../../assets/magnifier.png';

function IndustryCompanyTable({ companiesData, loadingCompanies, showCompaniesTable, onStockClick }) {
  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    if (typeof num === 'number') {
      return num.toLocaleString();
    }
    return num;
  };

  const formatPercentage = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return `${num >= 0 ? '+' : ''}${num}%`;
  };

  // 종목 클릭 핸들러
  const handleStockClick = (ticker) => {
    if (onStockClick) {
      onStockClick(ticker);
    }
  };

  if (!showCompaniesTable) {
    return null;
  }

  return (
    <div className="industry-companies-section">
      {loadingCompanies ? (
        <div className="industry-companies-loading">
          기업 정보를 불러오는 중...
        </div>
      ) : companiesData && companiesData.companies && companiesData.companies.length > 0 ? (
        <div style={{ marginTop: '16px', marginBottom: '16px' }}>
          <table className="companies-table">
            <thead className="companies-table-header">
              <tr className="companies-table-header-row">
                <th className="companies-table-header-cell ticker-header" rowSpan="2">티커</th>
                <th className="companies-table-header-cell" rowSpan="2">금요일 종가($)</th>
                <th className="companies-table-header-cell" rowSpan="2">시가총액(M$)</th>
                <th className="companies-table-header-cell" colSpan="3">수익률</th>
                <th className="companies-table-header-cell roe-header" colSpan="3">Valuation 지표</th>
              </tr>
              <tr className="companies-table-header-row">
                <th className="companies-table-header-cell">1W</th>
                <th className="companies-table-header-cell">1M</th>
                <th className="companies-table-header-cell">1Y</th>
                <th className="companies-table-header-cell">P/E(배)</th>
                <th className="companies-table-header-cell">P/B(배)</th>
                <th className="companies-table-header-cell roe-header">ROE(%)</th>
              </tr>
            </thead>
            <tbody className="companies-table-body">
              {companiesData.companies.map((company, index) => (
                <tr key={company.ticker} className={`companies-table-row ${index === companiesData.companies.length - 1 ? 'last-row' : ''}`}>
                  <td className="companies-table-cell ticker-cell" style={{ textAlign: 'center' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center', width: '100%' }}>
                      {company.ticker}
                      <button 
                        className="stock-magnifier-btn"
                        onClick={() => handleStockClick(company.ticker)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          padding: '2px',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                        title={`${company.ticker} 종목 상세로 이동`}
                      >
                        <img 
                          src={magnifierIcon} 
                          alt="상세보기"
                          style={{ width: '16px', height: '16px' }}
                        />
                      </button>
                    </span>
                  </td>
                  <td className="companies-table-cell">{company.current_price || 'N/A'}</td>
                  <td className="companies-table-cell">{formatNumber(company.market_cap_millions)}</td>
                  <td className={`companies-table-cell return-cell ${company.return_1week >= 0 ? 'positive' : 'negative'}`}>
                    {formatPercentage(company.return_1week)}
                  </td>
                  <td className={`companies-table-cell return-cell ${company.return_1month >= 0 ? 'positive' : 'negative'}`}>
                    {formatPercentage(company.return_1month)}
                  </td>
                  <td className={`companies-table-cell return-cell ${company.return_1year >= 0 ? 'positive' : 'negative'}`}>
                    {formatPercentage(company.return_1year)}
                  </td>
                  <td className="companies-table-cell">{company.pe_ratio || 'N/A'}</td>
                  <td className="companies-table-cell">{company.pb_ratio || 'N/A'}</td>
                  <td className="companies-table-cell roe-cell">{company.roe ?? 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="industry-companies-nodata">
          해당 산업의 기업 데이터가 없습니다.
        </div>
      )}
    </div>
  );
}

export default IndustryCompanyTable;
