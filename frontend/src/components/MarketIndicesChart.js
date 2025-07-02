import React from 'react';

const MarketIndicesChart = ({ data, loading, error }) => {
  if (loading) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #e9ecef'
      }}>
        주요 지수 데이터를 불러오는 중...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#d32f2f',
        backgroundColor: '#ffebee',
        borderRadius: '8px',
        border: '1px solid #ffcdd2'
      }}>
        지수 데이터를 불러오는데 실패했습니다: {error}
      </div>
    );
  }

  if (!data || (!data.dow && !data.sp500 && !data.nasdaq)) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #e9ecef'
      }}>
        주요 지수 데이터가 없습니다.
      </div>
    );
  }

  // 데이터가 있는 지수들만 필터링
  const indices = [];
  if (data.dow && data.dow.dates && data.dow.closes) {
    indices.push({ name: 'DOW', data: data.dow, color: '#1f77b4' });
  }
  if (data.sp500 && data.sp500.dates && data.sp500.closes) {
    indices.push({ name: 'S&P 500', data: data.sp500, color: '#ff7f0e' });
  }
  if (data.nasdaq && data.nasdaq.dates && data.nasdaq.closes) {
    indices.push({ name: 'NASDAQ', data: data.nasdaq, color: '#2ca02c' });
  }

  if (indices.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #e9ecef'
      }}>
        유효한 지수 데이터가 없습니다.
      </div>
    );
  }

  // 차트 크기 설정
  const width = 800;
  const height = 300;
  const padding = 50;

  // 모든 지수의 최대/최소값 계산 (정규화를 위해)
  let allValues = [];
  indices.forEach(index => {
    if (index.data.closes && index.data.closes.length > 0) {
      allValues = allValues.concat(index.data.closes);
    }
  });

  if (allValues.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666'
      }}>
        차트를 그릴 데이터가 없습니다.
      </div>
    );
  }

  const maxValue = Math.max(...allValues);
  const minValue = Math.min(...allValues);
  const valueRange = maxValue - minValue || 1;

  // 날짜 범위 계산 (첫 번째 지수의 날짜를 기준으로)
  const firstIndex = indices[0];
  const dateCount = firstIndex.data.dates.length;

  const xStep = (width - 2 * padding) / (dateCount - 1 || 1);
  const yScale = (value) => padding + ((maxValue - value) / valueRange) * (height - 2 * padding);

  return (
    <div style={{ 
      backgroundColor: '#ffffff',
      borderRadius: '8px',
      border: '1px solid #e0e0e0',
      padding: '20px',
      marginBottom: '20px'
    }}>
      <h3 style={{ 
        margin: '0 0 20px 0',
        fontSize: '18px',
        fontWeight: 'bold',
        color: '#333',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        📈 미국 주요 지수 (6개월)
      </h3>
      
      <div style={{ overflowX: 'auto' }}>
        <svg width={width} height={height} style={{ minWidth: '800px' }}>
          {/* 배경 격자 */}
          <defs>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f0f0f0" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width={width} height={height} fill="url(#grid)" />
          
          {/* Y축 */}
          <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#ccc" strokeWidth="1" />
          
          {/* X축 */}
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#ccc" strokeWidth="1" />
          
          {/* Y축 눈금 및 레이블 */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const value = minValue + ratio * valueRange;
            const y = padding + ratio * (height - 2 * padding);
            return (
              <g key={ratio}>
                <line x1={padding - 5} y1={y} x2={padding} y2={y} stroke="#ccc" strokeWidth="1" />
                <text x={padding - 10} y={y + 4} textAnchor="end" fontSize="11" fill="#666">
                  {value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </text>
              </g>
            );
          })}
          
          {/* 지수별 라인 그리기 */}
          {indices.map((index, indexIdx) => {
            const points = index.data.closes.map((close, i) => {
              const x = padding + i * xStep;
              const y = yScale(close);
              return `${x},${y}`;
            }).join(' ');

            return (
              <g key={index.name}>
                <polyline
                  fill="none"
                  stroke={index.color}
                  strokeWidth="2"
                  points={points}
                />
                {/* 범례 */}
                <line
                  x1={width - 150}
                  y1={padding + indexIdx * 20}
                  x2={width - 130}
                  y2={padding + indexIdx * 20}
                  stroke={index.color}
                  strokeWidth="3"
                />
                <text
                  x={width - 125}
                  y={padding + indexIdx * 20 + 4}
                  fontSize="12"
                  fill="#333"
                >
                  {index.name}
                </text>
              </g>
            );
          })}
          
          {/* X축 날짜 레이블 (일부만) */}
          {firstIndex.data.dates.map((date, i) => {
            if (i % Math.ceil(dateCount / 6) === 0) {
              const x = padding + i * xStep;
              return (
                <text
                  key={i}
                  x={x}
                  y={height - padding + 20}
                  textAnchor="middle"
                  fontSize="11"
                  fill="#666"
                >
                  {new Date(date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
                </text>
              );
            }
            return null;
          })}
        </svg>
      </div>
      
      {/* 간단한 요약 */}
      <div style={{ 
        marginTop: '16px',
        padding: '12px',
        backgroundColor: '#f8f9fa',
        borderRadius: '6px',
        fontSize: '14px',
        color: '#555'
      }}>
        <strong>6개월 기간:</strong> {firstIndex.data.dates[0]} ~ {firstIndex.data.dates[firstIndex.data.dates.length - 1]}
      </div>
    </div>
  );
};

export default MarketIndicesChart;
