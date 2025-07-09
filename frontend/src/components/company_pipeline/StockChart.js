import React, { useState, useEffect } from 'react';
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
import { fetchCombinedStockChart, fetchStockChartSummary } from '../../api/stockChart';
import './StockChart.css';

const StockChart = ({ symbol, startDate, endDate }) => {
  const [chartData, setChartData] = useState([]);
  const [chartSummary, setChartSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPeriod, setSelectedPeriod] = useState('6M');
  const [showPeriodOptions, setShowPeriodOptions] = useState(false);

  const periodOptions = [
    { value: '1W', label: '1주' },
    { value: '1M', label: '1개월' },
    { value: '3M', label: '3개월' },
    { value: '6M', label: '6개월' },
    { value: '1Y', label: '1년' }
  ];

  // 기간에 따른 날짜 계산
  const calculateDateRange = (period, endDate) => {
    const end = new Date(endDate);
    const start = new Date(end);
    
    switch (period) {
      case '1W':
        start.setDate(end.getDate() - 7);
        break;
      case '1M':
        start.setMonth(end.getMonth() - 1);
        break;
      case '3M':
        start.setMonth(end.getMonth() - 3);
        break;
      case '6M':
        start.setMonth(end.getMonth() - 6);
        break;
      case '1Y':
        start.setFullYear(end.getFullYear() - 1);
        break;
      default:
        start.setMonth(end.getMonth() - 1);
    }
    
    return {
      startDate: start.toISOString().split('T')[0],
      endDate: end.toISOString().split('T')[0]
    };
  };

  // 차트 데이터 로드
  const loadChartData = async () => {
    if (!symbol) return;
    
    setLoading(true);
    setError('');
    
    try {
      const { startDate: calcStartDate, endDate: calcEndDate } = calculateDateRange(selectedPeriod, endDate);
      const fixedChartTypes = ['price', 'volume'];
      
      console.log('🚀 Loading chart data:', { 
        symbol, 
        period: selectedPeriod,
        types: fixedChartTypes, 
      });
      
      // 차트 데이터와 요약 정보를 동시에 가져오기
      const [data, summaryData] = await Promise.all([
        fetchCombinedStockChart(
          symbol, 
          calcStartDate, 
          calcEndDate, 
          fixedChartTypes,
        ),
        fetchStockChartSummary(symbol, calcStartDate, calcEndDate)
      ]);
      
      console.log('📦 Received chart data:', data);
      
      // 차트 데이터 변환
      const transformedData = data.dates.map((date, index) => {
        const item = { date };
        
        // 주가 데이터
        if (data.data.price) {
          item.close = data.data.price.closes[index];
          item.open = data.data.price.opens[index];
          item.high = data.data.price.highs[index];
          item.low = data.data.price.lows[index];
        }
        
        // 거래량 데이터
        if (data.data.volume) {
          item.volume = data.data.volume.volumes[index];
        }
        
        return item;
      });
      
      console.log('🎯 Transformed data sample:', transformedData.slice(0, 3));
      
      setChartData(transformedData);
      setChartSummary(summaryData);
    } catch (err) {
      setError('차트 데이터를 불러오는데 실패했습니다: ' + err.message);
      console.error('Chart data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 기간이나 차트 타입이 변경될 때 데이터 새로고침
  useEffect(() => {
    loadChartData();
  }, [symbol, selectedPeriod]);

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

  // 기존에는 모든 내용을 stock-chart-container로 감쌌으나, 이제 각각의 요소를 개별적으로 렌더링
  return (
    <>
      {/* 차트 요약 정보 */}
      {chartSummary && (
        <div className="chart-summary">
          <div className="summary-grid summary-grid-2rows">
            {/* 첫 번째 행: 기간, 시작가, 종가 */}
            <div className="summary-item">
              <span className="summary-label">기간:</span>
              <span className="summary-value period-dropdown-wrapper" style={{ position: 'relative' }}>
                <button
                  className="period-dropdown-btn"
                  onClick={() => setShowPeriodOptions((prev) => !prev)}
                  style={{ cursor: 'pointer', background: 'none', border: 'none', padding: 0, color: '#2563eb', fontWeight: 'bold' }}
                >
                  {periodOptions.find(opt => opt.value === selectedPeriod)?.label || chartSummary.period}
                  <span style={{ marginLeft: 4 }}>▼</span>
                </button>
                {showPeriodOptions && (
                  <div className="period-dropdown-menu" style={{ position: 'absolute', zIndex: 10, background: '#fff', border: '1px solid #ddd', borderRadius: 4, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', marginTop: 4, minWidth: 120, width: 140 }}>
                    {periodOptions.map(option => (
                      <button
                        key={option.value}
                        className={`control-btn period-btn${selectedPeriod === option.value ? ' active' : ''}`}
                        style={{ display: 'block', width: '100%', textAlign: 'left', padding: '6px 16px', background: 'none', border: 'none', color: selectedPeriod === option.value ? '#2563eb' : '#222', fontWeight: selectedPeriod === option.value ? 'bold' : 'normal', cursor: 'pointer' }}
                        onClick={() => {
                          setSelectedPeriod(option.value);
                          setShowPeriodOptions(false);
                        }}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                )}
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">시작가:</span>
              <span className="summary-value">${chartSummary.start_price}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">종가:</span>
              <span className="summary-value">${chartSummary.end_price}</span>
            </div>
            {/* 두 번째 행: 변화, 최고가, 최저가 */}
            <div className="summary-item">
              <span className="summary-label">변화:</span>
              <span className={`summary-value ${chartSummary.change >= 0 ? 'positive' : 'negative'}`}>
                {chartSummary.change >= 0 ? '+' : ''}${chartSummary.change} ({chartSummary.change_pct >= 0 ? '+' : ''}{chartSummary.change_pct}%)
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">최고가:</span>
              <span className="summary-value">${chartSummary.high}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">최저가:</span>
              <span className="summary-value">${chartSummary.low}</span>
            </div>
          </div>
        </div>
      )}
      {/* 컨트롤 섹션 */}
      <div className="stock-chart-controls" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '24px' }}>
        {/* 차트 타입 버튼 제거됨 */}
      </div>
      {/* 차트 */}
      <div className="stock-chart-wrapper">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
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
              
              {/* 주가용 Y축 (왼쪽) */}
              <YAxis 
                yAxisId="price" 
                orientation="left"
                tick={{ fontSize: 12 }}
                tickFormatter={formatPrice}
                label={{ value: '주가 ($)', angle: -90, position: 'insideLeft' }}
              />
              
              {/* 거래량용 Y축 (오른쪽) - 거래량이 선택된 경우 */}
              <YAxis 
                yAxisId="volume" 
                orientation="right"
                tick={{ fontSize: 12 }}
                tickFormatter={formatVolume}
                label={{ value: '거래량', angle: 90, position: 'insideRight' }}
              />
              
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* 주가 라인 */}
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="close"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                name="종가"
              />
              
              {/* 거래량 바 차트 */}
              <Bar
                yAxisId="volume"
                dataKey="volume"
                fill="#94a3b8"
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
