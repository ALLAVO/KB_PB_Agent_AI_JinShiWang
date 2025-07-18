import React from 'react';
import { 
  ComposedChart, 
  Line, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import './StockChart.css';

const StockChart = ({ chartData, chartSummary, loading, error, selectedPeriod, onPeriodChange }) => {
  const periodOptions = [
    { value: '1W', label: '1주' },
    { value: '1M', label: '1개월' },
    { value: '3M', label: '3개월' },
    { value: '6M', label: '6개월' },
    { value: '1Y', label: '1년' }
  ];

  // 거래량 포맷터
  const formatVolume = (value) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value;
  };

  // 주가 포맷터
  const formatPrice = (value) => {
    return `$${value}`;
  };

  // 시가총액 포맷터
  const formatMarketCap = (value) => {
    if (value >= 1000000000000) {
      return `$${(value / 1000000000000).toFixed(2)}T`;
    } else if (value >= 1000000000) {
      return `$${(value / 1000000000).toFixed(2)}B`;
    } else if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(2)}K`;
    }
    return `$${value}`;
  };

  // 주식수 포맷터
  const formatShares = (value) => {
    if (value >= 1000000000) {
      return `${(value / 1000000000).toFixed(2)}B`;
    } else if (value >= 1000000) {
      return `${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(2)}K`;
    }
    return value;
  };

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="stock-chart-tooltip">
          <p className="tooltip-label">{`날짜: ${label}`}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.name}: ${entry.name === 'volume' ? formatVolume(entry.value) : `$${entry.value.toFixed(3)}`}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return <div className="stock-chart-loading">차트 데이터를 불러오는 중...</div>;
  }

  if (error) {
    return <div className="stock-chart-error">{error}</div>;
  }

  return (
    <>
      {/* 차트 요약 정보 */}
      {chartSummary && (
        <div className="chart-summary">
          <div className="summary-grid summary-grid-4rows">
            {/* 1행: 현재가-평균거래량-52주 최고가-1M 변동성 */}
            <div className="summary-item">
              <span className="summary-label">현재가:</span>
              <span className="summary-value">${chartSummary.current_price || chartSummary.end_price}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">평균거래량(60일):</span>
              <span className="summary-value">{chartSummary.avg_volume_60d ? formatVolume(chartSummary.avg_volume_60d) : 'N/A'}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">52주 최고가:</span>
              <span className="summary-value">${chartSummary.week_52_high || 'N/A'}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">1M변동성:</span>
              <span className="summary-value">{chartSummary.volatility_1m ? `${chartSummary.volatility_1m}%` : 'N/A'}</span>
            </div>
            {/* 2행: 시가총액-유동주식수-52주 최저가-1Y변동성 */}
            <div className="summary-item">
              <span className="summary-label">시가총액:</span>
              <span className="summary-value">{chartSummary.market_cap ? formatMarketCap(chartSummary.market_cap) : 'N/A'}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">유동주식수:</span>
              <span className="summary-value">{chartSummary.float_shares ? formatShares(chartSummary.float_shares) : 'N/A'}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">52주 최저가:</span>
              <span className="summary-value">${chartSummary.week_52_low || 'N/A'}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">1Y변동성:</span>
              <span className="summary-value">{chartSummary.volatility_1y ? `${chartSummary.volatility_1y}%` : 'N/A'}</span>
            </div>
          </div>
        </div>
      )}
      {/* 기간 버튼 컨트롤 섹션 */}
      <div className="stock-chart-controls">
        <div className="control-buttons control-buttons-right">
          {periodOptions.map(option => (
            <button
              key={option.value}
              className={`control-btn period-btn${selectedPeriod === option.value ? ' active' : ''}`}
              onClick={() => onPeriodChange(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
      {/* 차트 */}
      <div className="stock-chart-wrapper">
        {chartData && chartData.length > 0 ? (
          <ResponsiveContainer width="103%" height={400}>
            <ComposedChart data={chartData} margin={{ top: 20, right: 80, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis 
                yAxisId="price" 
                orientation="left"
                tick={{ fontSize: 12 }}
                tickFormatter={formatPrice}
                label={{ value: '주가 ($)', angle: -90, position: 'insideLeft' }}
              />
              <YAxis 
                yAxisId="volume" 
                orientation="right"
                tick={{ fontSize: 12 }}
                tickFormatter={formatVolume}
                label={{ value: '거래량', angle: 90, position: 'insideRight' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="close"
                stroke="#EFC352"
                strokeWidth={2}
                dot={false}
                name="종가"
              />
              <Bar
                yAxisId="volume"
                dataKey="volume"
                fill="#988A7C"
                opacity={0.6}
                name="거래량"
              />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div className="no-chart-data">차트 데이터가 없습니다.</div>
        )}
      </div>
    </>
  );
};

export default StockChart;
