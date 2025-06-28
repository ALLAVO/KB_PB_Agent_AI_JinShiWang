import React, { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { fetchCombinedReturnChart } from '../api/returnAnalysis';

const ReturnAnalysisChart = ({ symbol, startDate, endDate }) => {
  const [chartData, setChartData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState('index'); // 'index' or 'return'
  const [selectedPeriod, setSelectedPeriod] = useState('1M'); // 독립적인 기간 선택 상태

  // 기간 옵션 (주가 차트와 동일하지만 독립적)
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

  // 상대수익률 성과 평가 함수
  const getPerformanceEvaluation = (relativeReturn) => {
    if (relativeReturn > 0) {
      return { text: '벤치마크 대비 우수', color: '#28a745' };
    } else if (relativeReturn < 0) {
      return { text: '벤치마크 대비 저조', color: '#dc3545' };
    } else {
      return { text: '벤치마크와 동일', color: '#6c757d' };
    }
  };

  // 차트 데이터 로드
  const loadReturnData = async () => {
    if (!symbol) return;
    
    setLoading(true);
    setError('');
    
    try {
      const { startDate: calcStartDate, endDate: calcEndDate } = calculateDateRange(selectedPeriod, endDate);
      
      const data = await fetchCombinedReturnChart(symbol, calcStartDate, calcEndDate);
      
      // 차트 데이터 변환
      const transformedData = data.chart_data.dates.map((date, index) => ({
        date,
        stock_index: data.chart_data.stock_index[index] / 100, // 100 기준을 1 기준으로 변환
        nasdaq_index: data.chart_data.nasdaq_index[index] / 100, // 100 기준을 1 기준으로 변환
        relative_index: data.chart_data.relative_index[index] / 100, // 100 기준을 1 기준으로 변환
        stock_return: data.chart_data.stock_returns[index],
        nasdaq_return: data.chart_data.nasdaq_returns[index],
        relative_return: data.chart_data.relative_returns[index]
      }));
      
      setChartData(transformedData);
      setSummary(data.summary);
    } catch (err) {
      setError('수익률 데이터를 불러오는데 실패했습니다: ' + err.message);
      console.error('Return analysis data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 수익률 분석 차트만의 독립적인 기간 변경 감지
  useEffect(() => {
    loadReturnData();
  }, [symbol, selectedPeriod]); // endDate 제거하여 주가 차트와 독립

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="return-chart-tooltip">
          <p className="tooltip-label">{`날짜: ${label}`}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value.toFixed(3)}${viewMode === 'return' ? '%' : ''}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Y축 포맷터
  const formatYAxis = (value) => {
    return viewMode === 'return' ? `${value.toFixed(1)}%` : value.toFixed(2);
  };

  if (loading) {
    return <div className="return-chart-loading">수익률 데이터를 불러오는 중...</div>;
  }

  if (error) {
    return <div className="return-chart-error">{error}</div>;
  }

  return (
    <div className="return-chart-container">
      <div className="return-chart-header">
        <h3>{symbol} 수익률 분석</h3>
        <div className="view-mode-toggle">
          <button
            className={`toggle-btn ${viewMode === 'index' ? 'active' : ''}`}
            onClick={() => setViewMode('index')}
          >
            지수 보기
          </button>
          <button
            className={`toggle-btn ${viewMode === 'return' ? 'active' : ''}`}
            onClick={() => setViewMode('return')}
          >
            수익률 보기
          </button>
        </div>
      </div>

      {/* 수익률 분석 전용 기간 선택 컨트롤 */}
      <div className="return-chart-controls">
        <div className="control-section">
          <h4 className="control-title">기간:</h4>
          <div className="control-buttons">
            {periodOptions.map(option => (
              <button
                key={option.value}
                className={`control-btn period-btn ${selectedPeriod === option.value ? 'active' : ''}`}
                onClick={() => setSelectedPeriod(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 요약 정보 */}
      {summary && (
        <div className="return-summary">
          <div className="summary-grid">
            <div className="summary-item">
              <span className="summary-label">기간:</span>
              <span className="summary-value">
                {(() => {
                  const { startDate: calcStartDate, endDate: calcEndDate } = calculateDateRange(selectedPeriod, endDate);
                  return `${calcStartDate} ~ ${calcEndDate}`;
                })()}
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">{symbol} 수익률:</span>
              <span className={`summary-value ${summary.stock_return >= 0 ? 'positive' : 'negative'}`}>
                {summary.stock_return >= 0 ? '+' : ''}{summary.stock_return}%
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">나스닥 수익률:</span>
              <span className={`summary-value ${summary.nasdaq_return >= 0 ? 'positive' : 'negative'}`}>
                {summary.nasdaq_return >= 0 ? '+' : ''}{summary.nasdaq_return}%
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">초과 수익률:</span>
              <span className={`summary-value ${summary.outperformance >= 0 ? 'positive' : 'negative'}`}>
                {summary.outperformance >= 0 ? '+' : ''}{summary.outperformance}%
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">변동성:</span>
              <span className="summary-value">{summary.stock_volatility}%</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">성과 평가:</span>
              <span 
                className="summary-value"
                style={{ 
                  color: getPerformanceEvaluation(summary.relative_return).color,
                  fontWeight: 'bold'
                }}
              >
                {getPerformanceEvaluation(summary.relative_return).text}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 차트 */}
      <div className="return-chart-wrapper">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData} margin={{ top: 20, right: 80, bottom: 20, left: 20 }}>
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
                tick={{ fontSize: 12 }}
                tickFormatter={formatYAxis}
                label={{ 
                  value: viewMode === 'return' ? '수익률 (%)' : '지수 (기준=1)', 
                  angle: -90, 
                  position: 'insideLeft' 
                }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* 개별 주식 라인 */}
              <Line
                type="monotone"
                dataKey={viewMode === 'return' ? 'stock_return' : 'stock_index'}
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                name={`${symbol} ${viewMode === 'return' ? '수익률' : '지수'}`}
              />
              
              {/* 나스닥 라인 */}
              <Line
                type="monotone"
                dataKey={viewMode === 'return' ? 'nasdaq_return' : 'nasdaq_index'}
                stroke="#6b7280"
                strokeWidth={2}
                dot={false}
                name={`나스닥 ${viewMode === 'return' ? '수익률' : '지수'}`}
              />
              
              {/* 상대수익률 라인 */}
              <Line
                type="monotone"
                dataKey={viewMode === 'return' ? 'relative_return' : 'relative_index'}
                stroke="#dc2626"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name={`상대${viewMode === 'return' ? '수익률' : '지수'}`}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="no-return-data">수익률 데이터가 없습니다.</div>
        )}
      </div>
    </div>
  );
};

export default ReturnAnalysisChart;
