import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { fetchCombinedReturnChart } from '../../api/returnAnalysis';
import './ReturnAnalysisChart.css';

const ReturnAnalysisChart = ({ symbol, startDate, endDate }) => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 6개월 고정 기간 계산
  const calculate6MDateRange = (endDate) => {
    const end = new Date(endDate);
    const start = new Date(end);
    start.setMonth(end.getMonth() - 6);
    return {
      startDate: start.toISOString().split('T')[0],
      endDate: end.toISOString().split('T')[0]
    };
  };

  // 차트 데이터 로드
  const loadReturnData = async () => {
    if (!symbol) return;
    setLoading(true);
    setError('');
    try {
      const { startDate: calcStartDate, endDate: calcEndDate } = calculate6MDateRange(endDate);
      const data = await fetchCombinedReturnChart(symbol, calcStartDate, calcEndDate);
      // 차트 데이터 변환 (주가와 벤치마크만)
      const transformedData = data.chart_data.dates.map((date, index) => ({
        date,
        stock_index: data.chart_data.stock_index[index],
        benchmark_index: data.chart_data.nasdaq_index[index]
      }));
      setChartData(transformedData);
    } catch (err) {
      setError('수익률 데이터를 불러오는데 실패했습니다: ' + err.message);
      console.error('Return analysis data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReturnData();
    // eslint-disable-next-line
  }, [symbol, endDate]);

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="return-chart-tooltip">
          <p className="tooltip-label">{`날짜: ${label}`}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value.toFixed(2)}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return <div className="return-chart-loading">수익률 데이터를 불러오는 중...</div>;
  }
  if (error) {
    return <div className="return-chart-error">{error}</div>;
  }

  return (
    <div className="return-chart-container">
      <div className="return-chart-wrapper">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData} margin={{ top: 20, right: 40, bottom: 20, left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              {/* 좌측 Y축: 벤치마크(%) */}
              <YAxis
                yAxisId="left"
                orientation="left"
                tick={{ fontSize: 12 }}
                label={{ value: 'S&P500 상대 수익률(%)', angle: -90, position: 'insideLeft', dx: -10, dy: 100 }}
                domain={['auto', 'auto']}
                stroke="#999"
              />
              {/* 우측 Y축: 주가(천원) */}
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                label={{ value: '주가($)', angle: 90, position: 'insideRight', dx: 10, dy: 20 }}
                domain={['auto', 'auto']}
                stroke="#1e3a5c"
              />
              <Tooltip content={<CustomTooltip />} />
              {/* <Legend verticalAlign="top" height={36} /> */}
              {/* 벤치마크 라인 */}
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="benchmark_index"
                stroke="#988A7C"
                strokeWidth={3}
                dot={false}
                name="S&P500 상대 수익률 (좌측)"
              />
              {/* 주가 라인 */}
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="stock_index"
                stroke="#EFC352"
                strokeWidth={3}
                dot={false}
                name={`${symbol} 주가 (우측)`}
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
