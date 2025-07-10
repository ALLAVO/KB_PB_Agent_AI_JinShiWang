import React from 'react';
import './FinancialMetrics.css';

function FinancialMetrics({ loading, error, financialMetrics }) {
  if (loading) {
    return (
      <div className="financial-metrics-container">
        <div className="loading-spinner">재무지표 로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="financial-metrics-container">
        <div className="error-message">재무지표를 불러오지 못했습니다.</div>
      </div>
    );
  }

  if (!financialMetrics || !financialMetrics.metrics) {
    return (
      <div className="financial-metrics-container">
        <div className="no-data-message">재무지표 데이터가 없습니다.</div>
      </div>
    );
  }

  const { current_year, previous_year, metrics } = financialMetrics;

  // 값 포맷 (억 단위)
  const formatValue = (value) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      return `${(value / 100000000).toLocaleString()}억`;
    }
    return '-';
  };

  // 퍼센트 포맷
  const formatPercent = (value) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      return `${value.toFixed(1)}%`;
    }
    return '-';
  };

  // 표 데이터 구성
  const rows = [
    {
      label: '매출액',
      current: formatValue(metrics.revenue.current),
      previous: formatValue(metrics.revenue.previous),
    },
    {
      label: '영업이익',
      current: formatValue(metrics.operating_income.current),
      previous: formatValue(metrics.operating_income.previous),
    },
    {
      label: '영업이익률',
      current: formatPercent(metrics.operating_margin.current),
      previous: formatPercent(metrics.operating_margin.previous),
    },
    {
      label: '순이익',
      current: formatValue(metrics.net_income.current),
      previous: formatValue(metrics.net_income.previous),
    }
  ];

  return (
    <div className="financial-metrics-container">
      <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, background: 'white', borderRadius: '10px', overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
        <thead style={{ background: 'rgba(234,227,215,0.7)' }}>
          <tr style={{ height: 56 }}>
            <th style={{ padding: '18px 0', textAlign: 'center', fontWeight: 500, fontSize: '1.1rem', color: '#363532', border: 'none', letterSpacing: '-1px', minWidth: 80, borderTopLeftRadius: '6px', borderBottom: '1.5px solid #e5dfd3' }}>지표</th>
            <th style={{ padding: '18px 0', textAlign: 'center', fontWeight: 500, fontSize: '1.1rem', color: '#363532', border: 'none', letterSpacing: '-1px', minWidth: 100, borderBottom: '1.5px solid #e5dfd3' }}>{current_year}년</th>
            <th style={{ padding: '18px 0', textAlign: 'center', fontWeight: 500, fontSize: '1.1rem', color: '#363532', border: 'none', letterSpacing: '-1px', minWidth: 100, borderBottom: '1.5px solid #e5dfd3' }}>{previous_year}년</th>
          </tr>
        </thead>
        <tbody style={{ background: '#fff' }}>
          {rows.map((row, idx) => (
            <tr key={row.label} style={{ background: '#fff', borderBottom: idx < rows.length - 1 ? '1.5px solid #ede9e2' : 'none', height: 44 }}>
              <td style={{ padding: '8px 0', textAlign: 'center', fontWeight: 500, fontSize: '1.1rem', color: '#363532', letterSpacing: '-1px', borderBottomLeftRadius: idx === rows.length - 1 ? '6px' : 0 }}>{row.label}</td>
              <td style={{ padding: '8px 0', textAlign: 'center', fontWeight: 400, fontSize: '1.1rem', color: '#363532', letterSpacing: '-1px' }}>{row.current}</td>
              <td style={{ padding: '8px 0', textAlign: 'center', fontWeight: 400, fontSize: '1.1rem', color: '#363532', letterSpacing: '-1px' }}>{row.previous}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default FinancialMetrics;
