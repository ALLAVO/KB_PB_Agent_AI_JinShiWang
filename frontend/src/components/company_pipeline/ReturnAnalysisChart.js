import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import './ReturnAnalysisChart.css';

const ReturnAnalysisChart = ({ chartData, tableData, loading, error, symbol }) => {
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
        {chartData && chartData.length > 0 ? (
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
        <div style={{ marginTop: '16px', marginBottom: '16px' }}>
          <table style={{
            width: '100%',
            borderCollapse: 'separate',
            borderSpacing: 0,
            background: 'white',
            borderRadius: '10px',
            overflow: 'hidden',
            boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
          }}>
            <thead style={{ background: 'rgba(234,227,215,0.7)', borderRadius: '6px 6px 0 0' }}>
              <tr style={{ background: 'rgba(234,227,215,0.7)', height: 40 }}>
                <th style={{
                  padding: '24px 0 24px 0',
                  textAlign: 'center',
                  fontWeight: 500,
                  fontSize: '1.2rem',
                  color: '#363532',
                  border: 'none',
                  letterSpacing: '-1px',
                  minWidth: 80,
                  borderTopLeftRadius: '6px',
                  borderBottom: '1.5px solid #e5dfd3',
                }}></th>
                {['1M', '3M', '6M', '12M'].map((period, idx) => (
                  <th key={period} style={{
                    padding: '24px 0 24px 0',
                    textAlign: 'center',
                    fontWeight: 500,
                    fontSize: '1.2rem',
                    color: '#363532',
                    border: 'none',
                    letterSpacing: '-1px',
                    minWidth: 80,
                    borderBottom: '1.5px solid #e5dfd3',
                    borderTopRightRadius: idx === 3 ? '6px' : 0,
                  }}>{period}</th>
                ))}
              </tr>
            </thead>
            <tbody style={{ background: '#fff', borderRadius: '0 0 6px 6px' }}>
              <tr style={{
                background: '#fff',
                borderBottom: '1.5px solid #ede9e2',
                height: 44
              }}>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500,
                  fontSize: '1.2rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                  borderBottomLeftRadius: '6px',
                }}><strong>절대수익률</strong></td>
                {['1M', '3M', '6M', '12M'].map((period, idx) => {
                  const row = tableData.table_data.find(r => r.period === period);
                  const value = row?.absolute_return;
                  let color = '#363532';
                  if (value > 0) color = '#ef4444';
                  else if (value < 0) color = '#2563eb';
                  return (
                    <td key={period} style={{
                      padding: '6px 0',
                      textAlign: 'center',
                      fontWeight: 500,
                      fontSize: '1.2rem',
                      color: value !== null && value !== undefined ? color : '#363532',
                      letterSpacing: '-1px',
                      borderBottomRightRadius: idx === 3 ? '6px' : 0,
                    }}>
                      {value !== null && value !== undefined ? value.toFixed(1) : '-'}
                    </td>
                  );
                })}
              </tr>
              <tr style={{
                background: '#fff',
                height: 44
              }}>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500,
                  fontSize: '1.2rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                  borderBottomLeftRadius: '6px',
                }}><strong>상대수익률</strong></td>
                {['1M', '3M', '6M', '12M'].map((period, idx) => {
                  const row = tableData.table_data.find(r => r.period === period);
                  const value = row?.relative_return;
                  let color = '#363532';
                  if (value > 0) color = '#ef4444';
                  else if (value < 0) color = '#2563eb';
                  return (
                    <td key={period} style={{
                      padding: '6px 0',
                      textAlign: 'center',
                      fontWeight: 500,
                      fontSize: '1.2rem',
                      color: value !== null && value !== undefined ? color : '#363532',
                      letterSpacing: '-1px',
                      borderBottomRightRadius: idx === 3 ? '6px' : 0,
                    }}>
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
