import React from 'react';
import './ValuationMetrics.css';

function ValuationMetrics({ loading, error, valuationMetrics }) {
  if (loading) {
    return (
      <div className="valuation-metrics-table-container">
        <div className="valuation-loading">벨류에이션 지표를 불러오는 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="valuation-metrics-table-container">
        <div className="valuation-error">벨류에이션 지표를 불러올 수 없습니다: {error}</div>
      </div>
    );
  }

  if (!valuationMetrics || !valuationMetrics.metrics) {
    return (
      <div className="valuation-metrics-table-container">
        <div className="valuation-no-data">벨류에이션 지표 데이터가 없습니다.</div>
      </div>
    );
  }

  const { metrics, current_year, previous_year } = valuationMetrics;

  const formatValue = (value, suffix = '') => {
    if (value === null || value === undefined || isNaN(value)) return '-';
    return `${value}${suffix}`;
  };

  const rows = [
    {
      label: 'EPS',
      current: metrics.eps?.current,
      previous: metrics.eps?.previous,
      suffix: '$',
    },
    {
      label: 'P/E Ratio',
      current: metrics.pe_ratio?.current,
      previous: metrics.pe_ratio?.previous,
      suffix: '배',
    },
    {
      label: 'P/B Ratio',
      current: metrics.pb_ratio?.current,
      previous: metrics.pb_ratio?.previous,
      suffix: '배',
    },
    {
      label: 'ROE',
      current: metrics.roe_percent?.current,
      previous: metrics.roe_percent?.previous,
      suffix: '%',
    },
  ];

  return (
    <div className="valuation-metrics-table-container">
      <table className="valuation-metrics-table">
        <thead>
          <tr>
            <th className="valuation-th label">구분</th>
            <th className="valuation-th">{current_year}년</th>
            <th className="valuation-th">{previous_year}년</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="valuation-tr">
              <td className="valuation-td label">{row.label}</td>
              <td className="valuation-td value">{formatValue(row.current, row.suffix)}</td>
              <td className="valuation-td value">{formatValue(row.previous, row.suffix)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ValuationMetrics;
