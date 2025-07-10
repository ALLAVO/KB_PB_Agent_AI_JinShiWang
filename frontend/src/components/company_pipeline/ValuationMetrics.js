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

  const getColorByChange = (value) => {
    if (value > 0) return '#ef4444'; // 빨간색 (상승)
    if (value < 0) return '#2563eb'; // 파란색 (하락)
    return '#363532'; // 기본색 (변화없음)
  };

  const getChange = (current, previous) => {
    if (
      current === null ||
      previous === null ||
      current === undefined ||
      previous === undefined ||
      isNaN(current) ||
      isNaN(previous) ||
      previous === 0
    ) {
      return null;
    }
    return ((current - previous) / Math.abs(previous) * 100);
  };

  const rows = [
    {
      label: 'EPS (주당순이익)',
      current: metrics.eps?.current,
      previous: metrics.eps?.previous,
      suffix: '$',
    },
    {
      label: 'P/E Ratio (주가수익비율)',
      current: metrics.pe_ratio?.current,
      previous: metrics.pe_ratio?.previous,
      suffix: '배',
    },
    {
      label: 'P/B Ratio (주가순자산비율)',
      current: metrics.pb_ratio?.current,
      previous: metrics.pb_ratio?.previous,
      suffix: '배',
    },
    {
      label: 'ROE (자기자본이익률)',
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
            <th className="valuation-th">등락률(%)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => {
            const change = getChange(row.current, row.previous);
            return (
              <tr key={row.label} className="valuation-tr">
                <td className="valuation-td label">{row.label}</td>
                <td className="valuation-td value">{formatValue(row.current, row.suffix)}</td>
                <td className="valuation-td value">{formatValue(row.previous, row.suffix)}</td>
                <td className="valuation-td value" style={{ color: getColorByChange(change) }}>
                  {change === null ? '-' : `${change > 0 ? '+' : ''}${change.toFixed(2)}%`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default ValuationMetrics;
