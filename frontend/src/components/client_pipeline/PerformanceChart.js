import React from 'react';

const PerformanceChart = ({ clientName, performanceData, loading }) => {
  return (
    <div>
      <div>
        {performanceData ? (
          <div>
            <div className="performance-summary" style={{ marginLeft: '40px', width: '770px' }}>
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
            
            <div className="performance-table-container" style={{ marginLeft: '40px', width: '800px' }}>
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
              <small className="coming-soon" style={{ textAlign: 'right', display: 'block' }}>* 성과 구간은 고객님 최근 리밸런싱 이후부터 지난주 금요일까지를 대상으로 합니다.</small>
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
  );
};

export default PerformanceChart;
