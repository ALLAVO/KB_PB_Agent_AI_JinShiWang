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
import ReturnAnalysisChart from '../ReturnAnalysisChart';
import './StockChart.css';

const StockChart = ({ symbol, startDate, endDate }) => {
  const [chartData, setChartData] = useState([]);
  const [chartSummary, setChartSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPeriod, setSelectedPeriod] = useState('6M');
  const [selectedChartTypes, setSelectedChartTypes] = useState(['price', 'moving_average', 'volume']);
  const [maPeriods, setMaPeriods] = useState([5, 60]);
  const [showPeriodOptions, setShowPeriodOptions] = useState(false);

  const periodOptions = [
    { value: '1W', label: '1주' },
    { value: '1M', label: '1개월' },
    { value: '3M', label: '3개월' },
    { value: '6M', label: '6개월' },
    { value: '1Y', label: '1년' }
  ];

  const chartTypeOptions = [
    { value: 'price', label: '주가' },
    { value: 'moving_average', label: '이동평균' },
    { value: 'volume', label: '거래량' }
  ];

  const maOptions = [
    { value: 5, label: '5일' },
    { value: 10, label: '10일' },
    { value: 20, label: '20일' },
    { value: 60, label: '60일' }
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
      
      console.log('🚀 Loading chart data:', { 
        symbol, 
        period: selectedPeriod,
        types: selectedChartTypes, 
        maPeriods 
      });
      
      // 차트 데이터와 요약 정보를 동시에 가져오기
      const [data, summaryData] = await Promise.all([
        fetchCombinedStockChart(
          symbol, 
          calcStartDate, 
          calcEndDate, 
          selectedChartTypes,
          maPeriods
        ),
        fetchStockChartSummary(symbol, calcStartDate, calcEndDate)
      ]);
      
      console.log('📦 Received chart data:', data);
      
      // 차트 데이터 변환
      const transformedData = data.dates.map((date, index) => {
        const item = { date };
        
        // 주가 데이터
        if (selectedChartTypes.includes('price') && data.data.price) {
          item.close = data.data.price.closes[index];
          item.open = data.data.price.opens[index];
          item.high = data.data.price.highs[index];
          item.low = data.data.price.lows[index];
        }
        
        // 이동평균 데이터
        if (selectedChartTypes.includes('moving_average') && data.data.moving_average) {
          console.log('📈 Processing MA data at index', index, ':', data.data.moving_average);
          maPeriods.forEach(period => {
            const maKey = `ma${period}`;
            if (data.data.moving_average[maKey]) {
              const maValue = data.data.moving_average[maKey][index];
              if (maValue !== null && maValue !== undefined && !isNaN(maValue)) {
                item[maKey] = Number(maValue);
                console.log(`✅ Set ${maKey}[${index}] = ${maValue}`);
              } else {
                console.log(`⚠️ Invalid ${maKey}[${index}] = ${maValue}`);
              }
            } else {
              console.log(`❌ No ${maKey} data available`);
            }
          });
        }
        
        // 거래량 데이터
        if (selectedChartTypes.includes('volume') && data.data.volume) {
          item.volume = data.data.volume.volumes[index];
        }
        
        return item;
      });
      
      console.log('🎯 Transformed data sample:', transformedData.slice(0, 3));
      console.log('📊 MA data in first item:', {
        ma5: transformedData[0]?.ma5,
        ma20: transformedData[0]?.ma20,
        ma60: transformedData[0]?.ma60
      });
      
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
  }, [symbol, selectedPeriod, selectedChartTypes, maPeriods]);

  // 차트 타입 토글
  const toggleChartType = (type) => {
    setSelectedChartTypes(prev => {
      if (prev.includes(type)) {
        return prev.filter(t => t !== type);
      } else {
        return [...prev, type];
      }
    });
  };

  // 이동평균 기간 토글
  const toggleMAPeriod = (period) => {
    setMaPeriods(prev => {
      if (prev.includes(period)) {
        return prev.filter(p => p !== period);
      } else {
        return [...prev, period].sort((a, b) => a - b);
      }
    });
  };

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
        {/* 차트 타입 + 이동평균 한 줄에 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px', width: '100%' }}>
          {/* 차트 타입 선택 */}
          <div className="control-section" style={{ marginBottom: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* <h4 className="control-title" style={{ margin: 0, marginRight: 8 }}>차트 타입:</h4> 갈색 작대기(제목) 제거 */}
            <div className="control-buttons" style={{ display: 'flex', gap: '4px' }}>
              {chartTypeOptions.map(option => (
                <button
                  key={option.value}
                  className={`control-btn chart-type-btn ${selectedChartTypes.includes(option.value) ? 'active' : ''}`}
                  onClick={() => toggleChartType(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          {/* 이동평균 기간 선택 (이동평균이 선택된 경우에만 표시) */}
          {selectedChartTypes.includes('moving_average') && (
            <div className="control-section" style={{ marginBottom: 0, display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'auto' }}>
              {/* <h4 className="control-title" style={{ margin: 0, marginRight: 8 }}>이동평균:</h4> 갈색 작대기(제목) 제거 */}
              <div className="control-buttons" style={{ display: 'flex', gap: '4px' }}>
                {maOptions.map(option => (
                  <button
                    key={option.value}
                    className={`control-btn ma-btn ${maPeriods.includes(option.value) ? 'active' : ''}`}
                    onClick={() => toggleMAPeriod(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
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
              {selectedChartTypes.includes('volume') && (
                <YAxis 
                  yAxisId="volume" 
                  orientation="right"
                  tick={{ fontSize: 12 }}
                  tickFormatter={formatVolume}
                  label={{ value: '거래량', angle: 90, position: 'insideRight' }}
                />
              )}
              
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* 주가 라인 */}
              {selectedChartTypes.includes('price') && (
                <Line
                  yAxisId="price"
                  type="monotone"
                  dataKey="close"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={false}
                  name="종가"
                />
              )}
              
              {/* 이동평균 라인들 */}
              {selectedChartTypes.includes('moving_average') && maPeriods.map((period, index) => {
                const colors = ['#ef4444', '#f97316', '#8b5cf6', '#10b981'];
                const dataKey = `ma${period}`;
                console.log(`🎨 Rendering MA line for ${dataKey}`);
                
                return (
                  <Line
                    key={dataKey}
                    yAxisId="price"
                    type="monotone"
                    dataKey={dataKey}
                    stroke={colors[index % colors.length]}
                    strokeWidth={2}
                    strokeDasharray="3 3"
                    dot={false}
                    name={`${period}일 이동평균`}
                    connectNulls={false}
                  />
                );
              })}
              
              {/* 거래량 바 차트 (상대지수가 선택되지 않은 경우에만) */}
              {selectedChartTypes.includes('volume') && (
                <Bar
                  yAxisId="volume"
                  dataKey="volume"
                  fill="#94a3b8"
                  opacity={0.6}
                  name="거래량"
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div className="no-chart-data">차트 데이터가 없습니다.</div>
        )}
      </div>
      {/* 수익률 분석 차트 - 주가 차트와 독립적으로 동작 */}
      <ReturnAnalysisChart 
        symbol={symbol}
        startDate={startDate}
        endDate={endDate}
      />
    </>
  );
};

export default StockChart;
