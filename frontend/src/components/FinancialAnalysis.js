import React from 'react';
import './FinancialAnalysis.css';

const FinancialAnalysis = ({ financialData, loading, error, symbol }) => {
  const formatValue = (value, unit) => {
    if (value === null || value === undefined || isNaN(value)) {
      return 'N/A';
    }
    
    if (unit === 'USD' && value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (unit === 'USD' && value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    } else if (unit === 'USD') {
      return `$${value.toLocaleString()}`;
    } else if (unit === '%') {
      return `${value.toFixed(2)}%`;
    } else if (unit === '배') {
      return `${value.toFixed(2)}`;
    }
    
    return typeof value === 'number' ? value.toLocaleString() : value;
  };

  const getValueClass = (value, unit) => {
    if (value === null || value === undefined || isNaN(value)) {
      return 'neutral';
    }
    
    if (unit === '%' || unit === '배') {
      return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
    }
    
    return 'neutral';
  };

  if (loading) {
    return (
      <div className="financial-analysis-section">
        <div className="financial-analysis-header">
          <div className="financial-analysis-title">
            <span>📊</span>
            <h3>재무 분석</h3>
          </div>
        </div>
        <div className="financial-loading">
          <span className="financial-loading-icon">⏳</span>
          재무 데이터를 불러오는 중...
        </div>
      </div>
    );
  }

  if (error && error !== '종목코드를 입력해주세요') {
    return (
      <div className="financial-analysis-section">
        <div className="financial-analysis-header">
          <div className="financial-analysis-title">
            <span>📊</span>
            <h3>재무 분석</h3>
          </div>
        </div>
        <div className="financial-error">
          재무 데이터를 불러오는데 실패했습니다.
        </div>
      </div>
    );
  }

  if (!financialData) {
    return (
      <div className="financial-analysis-section">
        <div className="financial-analysis-header">
          <div className="financial-analysis-title">
            <span>📊</span>
            <h3>재무 분석</h3>
          </div>
        </div>
        <div className="financial-no-data">
          재무 데이터가 없습니다.
        </div>
      </div>
    );
  }

  const { company_name, sector, industry, financial_health, profitability, valuation, stock_info, last_updated } = financialData;

  const renderFinancialTable = (title, data, icon) => (
    <div className="financial-category">
      <h4 className="financial-category-title">
        <span>{icon}</span>
        {title}
      </h4>
      <table className="financial-table">
        <thead>
          <tr>
            <th>지표</th>
            <th>값</th>
            <th>설명</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(data).map(([key, info]) => (
            <tr key={key}>
              <td className="metric-name">{key}</td>
              <td className={`metric-value ${getValueClass(info.value, info.unit)}`}>
                {formatValue(info.value, info.unit)}
                {info.unit && <span className="metric-unit">{info.unit}</span>}
              </td>
              <td className="metric-description">{info.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="financial-analysis-section">
      <div className="financial-analysis-header">
        <div className="financial-analysis-title">
          <span>📊</span>
          <h3>{company_name || symbol} 재무 분석</h3>
        </div>
        {sector && (
          <div className="company-info">
            <span className="sector-info">{sector}</span>
            {industry && <span className="industry-info"> | {industry}</span>}
          </div>
        )}
      </div>
      
      <div className="financial-analysis-content">
        {renderFinancialTable('재무 건전성', financial_health, '🛡️')}
        {renderFinancialTable('수익성 지표', profitability, '💰')}
        {renderFinancialTable('밸류에이션', valuation, '📈')}
        {renderFinancialTable('주가 정보', stock_info, '📊')}
        
        {last_updated && (
          <div className="last-updated">
            마지막 업데이트: {last_updated}
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialAnalysis;
