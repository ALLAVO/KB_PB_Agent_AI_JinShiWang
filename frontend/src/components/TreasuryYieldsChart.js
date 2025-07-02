import React from 'react';

const TreasuryYieldsChart = ({ data, loading, error }) => {
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
        국채 금리 데이터를 불러오는 중...
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
        국채 금리 데이터를 불러오는데 실패했습니다: {error}
      </div>
    );
  }

  if (!data || !data.dates || !data.us_2y || !data.us_10y) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #e9ecef'
      }}>
        국채 금리 데이터가 없습니다.
      </div>
    );
  }

  // 차트 크기 설정
  const width = 800;
  const height = 300;
  const padding = 50;

  // 모든 금리 값 수집
  const allYields = [...data.us_2y, ...data.us_10y].filter(val => val !== null && val !== undefined);
  
  if (allYields.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666'
      }}>
        유효한 금리 데이터가 없습니다.
      </div>
    );
  }

  const maxValue = Math.max(...allYields);
  const minValue = Math.min(...allYields);
  const valueRange = maxValue - minValue || 1;

  const dateCount = data.dates.length;
  const xStep = (width - 2 * padding) / (dateCount - 1 || 1);
  const yScale = (value) => {
    if (value === null || value === undefined) return null;
    return padding + ((maxValue - value) / valueRange) * (height - 2 * padding);
  };

  // 라인 포인트 생성 (null 값 제외)
  const create2YPoints = () => {
    const points = [];
    for (let i = 0; i < data.us_2y.length; i++) {
      if (data.us_2y[i] !== null && data.us_2y[i] !== undefined) {
        const x = padding + i * xStep;
        const y = yScale(data.us_2y[i]);
        if (y !== null) points.push(`${x},${y}`);
      }
    }
    return points.join(' ');
  };

  const create10YPoints = () => {
    const points = [];
    for (let i = 0; i < data.us_10y.length; i++) {
      if (data.us_10y[i] !== null && data.us_10y[i] !== undefined) {
        const x = padding + i * xStep;
        const y = yScale(data.us_10y[i]);
        if (y !== null) points.push(`${x},${y}`);
      }
    }
    return points.join(' ');
  };

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
        📊 미국 국채 금리 (6개월)
      </h3>
      
      <div style={{ overflowX: 'auto' }}>
        <svg width={width} height={height} style={{ minWidth: '800px' }}>
          {/* 배경 격자 */}
          <defs>
            <pattern id="grid-treasury" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f0f0f0" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width={width} height={height} fill="url(#grid-treasury)" />
          
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
                  {value.toFixed(2)}%
                </text>
              </g>
            );
          })}
          
          {/* 2년물 금리 라인 */}
          <polyline
            fill="none"
            stroke="#e74c3c"
            strokeWidth="2"
            points={create2YPoints()}
          />
          
          {/* 10년물 금리 라인 */}
          <polyline
            fill="none"
            stroke="#3498db"
            strokeWidth="2"
            points={create10YPoints()}
          />
          
          {/* 범례 */}
          <line x1={width - 150} y1={padding} x2={width - 130} y2={padding} stroke="#e74c3c" strokeWidth="3" />
          <text x={width - 125} y={padding + 4} fontSize="12" fill="#333">2년물</text>
          
          <line x1={width - 150} y1={padding + 20} x2={width - 130} y2={padding + 20} stroke="#3498db" strokeWidth="3" />
          <text x={width - 125} y={padding + 24} fontSize="12" fill="#333">10년물</text>
          
          {/* X축 날짜 레이블 (일부만) */}
          {data.dates.map((date, i) => {
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
        <strong>6개월 기간:</strong> {data.dates[0]} ~ {data.dates[data.dates.length - 1]} | 
        <strong> 최근 2년물:</strong> {data.us_2y[data.us_2y.length - 1]?.toFixed(2)}% | 
        <strong> 최근 10년물:</strong> {data.us_10y[data.us_10y.length - 1]?.toFixed(2)}%
      </div>
    </div>
  );
};

export default TreasuryYieldsChart;
