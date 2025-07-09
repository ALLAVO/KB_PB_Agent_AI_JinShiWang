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
  const [tableData, setTableData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 18개월 고정 기간 계산 (12M 데이터를 위해 충분한 기간 확보)
  const calculate18MDateRange = (endDate) => {
    const end = new Date(endDate);
    const start = new Date(end);
    start.setMonth(end.getMonth() - 18);
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
      const { startDate: calcStartDate, endDate: calcEndDate } = calculate18MDateRange(endDate);
      const data = await fetchCombinedReturnChart(symbol, calcStartDate, calcEndDate);
      
      // 차트용 데이터는 6개월만 표시 (최근 6개월)
      const sixMonthsAgo = new Date(endDate);
      sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
      const sixMonthsAgoStr = sixMonthsAgo.toISOString().split('T')[0];
      
      // 차트 데이터 변환 (6개월 데이터만 필터링)
      const transformedData = data.chart_data.dates
        .map((date, index) => ({
          date,
          stock_index: data.chart_data.stock_index[index],
          benchmark_index: data.chart_data.sp500_index[index]
        }))
        .filter(item => item.date >= sixMonthsAgoStr);
      
      setChartData(transformedData);
      setTableData(data.table_data);
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

  // 수익률 색상 결정
  const getReturnColor = (value) => {
    if (value > 0) return 'return-positive';
    if (value < 0) return 'return-negative';
    return 'return-neutral';
  };

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
      
      {/* 수익률 분석 표 */}
      {tableData && (
        <div className="return-analysis-table">
          <h3>주가수익률(%)</h3>
          <table className="return-table">
            <thead>
              <tr>
                <th></th>
                {['1M', '3M', '6M', '12M'].map((period) => (
                  <th key={period}>{period}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>절대수익률</strong></td>
                {['1M', '3M', '6M', '12M'].map((period) => {
                  const row = tableData.table_data.find(r => r.period === period);
                  const value = row?.absolute_return;
                  return (
                    <td key={period} className={value !== null && value !== undefined ? getReturnColor(value) : 'return-neutral'}>
                      {value !== null && value !== undefined ? value.toFixed(1) : '-'}
                    </td>
                  );
                })}
              </tr>
              <tr>
                <td><strong>상대수익률</strong></td>
                {['1M', '3M', '6M', '12M'].map((period) => {
                  const row = tableData.table_data.find(r => r.period === period);
                  const value = row?.relative_return;
                  return (
                    <td key={period} className={value !== null && value !== undefined ? getReturnColor(value) : 'return-neutral'}>
                      {value !== null && value !== undefined ? value.toFixed(1) : '-'}
                    </td>
                  );
                })}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ReturnAnalysisChart;
