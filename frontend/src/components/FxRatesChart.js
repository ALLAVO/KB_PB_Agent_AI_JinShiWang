import React from 'react';

const FxRatesChart = ({ data, loading, error }) => {
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
        환율 데이터를 불러오는 중...
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
        환율 데이터를 불러오는데 실패했습니다: {error}
      </div>
    );
  }

  if (!data || !data.dates || !data.usd_krw || !data.eur_usd) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #e9ecef'
      }}>
        환율 데이터가 없습니다.
      </div>
    );
  }

  // 차트 크기 설정
  const width = 800;
  const height = 300;
  const padding = 50;

  // USD/KRW와 EUR/USD는 스케일이 다르므로 정규화 필요
  const usdKrwValues = data.usd_krw.filter(val => val !== null && val !== undefined);
  const eurUsdValues = data.eur_usd.filter(val => val !== null && val !== undefined);
  
  if (usdKrwValues.length === 0 && eurUsdValues.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666'
      }}>
        유효한 환율 데이터가 없습니다.
      </div>
    );
  }

  const dateCount = data.dates.length;
  const xStep = (width - 2 * padding) / (dateCount - 1 || 1);

  // USD/KRW 정규화 (0-1 범위)
  const usdKrwMin = Math.min(...usdKrwValues);
  const usdKrwMax = Math.max(...usdKrwValues);
  const usdKrwRange = usdKrwMax - usdKrwMin || 1;

  // EUR/USD 정규화 (0-1 범위)
  const eurUsdMin = Math.min(...eurUsdValues);
  const eurUsdMax = Math.max(...eurUsdValues);
  const eurUsdRange = eurUsdMax - eurUsdMin || 1;

  const normalizeUsdKrw = (value) => {
    if (value === null || value === undefined) return null;
    return (value - usdKrwMin) / usdKrwRange;
  };

  const normalizeEurUsd = (value) => {
    if (value === null || value === undefined) return null;
    return (value - eurUsdMin) / eurUsdRange;
  };

  const yScale = (normalizedValue) => {
    if (normalizedValue === null) return null;
    return padding + (1 - normalizedValue) * (height - 2 * padding);
  };

  // 라인 포인트 생성
  const createUsdKrwPoints = () => {
    const points = [];
    for (let i = 0; i < data.usd_krw.length; i++) {
      const normalized = normalizeUsdKrw(data.usd_krw[i]);
      if (normalized !== null) {
        const x = padding + i * xStep;
        const y = yScale(normalized);
        if (y !== null) points.push(`${x},${y}`);
      }
    }
    return points.join(' ');
  };

  const createEurUsdPoints = () => {
    const points = [];
    for (let i = 0; i < data.eur_usd.length; i++) {
      const normalized = normalizeEurUsd(data.eur_usd[i]);
      if (normalized !== null) {
        const x = padding + i * xStep;
        const y = yScale(normalized);
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
        💱 환율 (6개월)
      </h3>
      
      <div style={{ overflowX: 'auto' }}>
        <svg width={width} height={height} style={{ minWidth: '800px' }}>
          {/* 배경 격자 */}
          <defs>
            <pattern id="grid-fx" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f0f0f0" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width={width} height={height} fill="url(#grid-fx)" />
          
          {/* Y축 */}
          <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#ccc" strokeWidth="1" />
          
          {/* X축 */}
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#ccc" strokeWidth="1" />
          
          {/* 정규화된 Y축 눈금 (0-100%) */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = padding + ratio * (height - 2 * padding);
            return (
              <g key={ratio}>
                <line x1={padding - 5} y1={y} x2={padding} y2={y} stroke="#ccc" strokeWidth="1" />
                <text x={padding - 10} y={y + 4} textAnchor="end" fontSize="11" fill="#666">
                  {((1 - ratio) * 100).toFixed(0)}%
                </text>
              </g>
            );
          })}
          
          {/* USD/KRW 라인 */}
          <polyline
            fill="none"
            stroke="#e67e22"
            strokeWidth="2"
            points={createUsdKrwPoints()}
          />
          
          {/* EUR/USD 라인 */}
          <polyline
            fill="none"
            stroke="#9b59b6"
            strokeWidth="2"
            points={createEurUsdPoints()}
          />
          
          {/* 범례 */}
          <line x1={width - 150} y1={padding} x2={width - 130} y2={padding} stroke="#e67e22" strokeWidth="3" />
          <text x={width - 125} y={padding + 4} fontSize="12" fill="#333">USD/KRW</text>
          
          <line x1={width - 150} y1={padding + 20} x2={width - 130} y2={padding + 20} stroke="#9b59b6" strokeWidth="3" />
          <text x={width - 125} y={padding + 24} fontSize="12" fill="#333">EUR/USD</text>
          
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
      
      {/* 실제 값을 보여주는 요약 */}
      <div style={{ 
        marginTop: '16px',
        padding: '12px',
        backgroundColor: '#f8f9fa',
        borderRadius: '6px',
        fontSize: '14px',
        color: '#555'
      }}>
        <div style={{ marginBottom: '8px' }}>
          <strong>6개월 기간:</strong> {data.dates[0]} ~ {data.dates[data.dates.length - 1]}
        </div>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div>
            <strong>USD/KRW:</strong> {data.usd_krw[data.usd_krw.length - 1]?.toLocaleString()} 
            (범위: {usdKrwMin.toLocaleString()} ~ {usdKrwMax.toLocaleString()})
          </div>
          <div>
            <strong>EUR/USD:</strong> {data.eur_usd[data.eur_usd.length - 1]?.toFixed(4)} 
            (범위: {eurUsdMin.toFixed(4)} ~ {eurUsdMax.toFixed(4)})
          </div>
        </div>
        <div style={{ marginTop: '8px', fontSize: '12px', color: '#888' }}>
          * 차트는 각 환율의 6개월 변동폭을 0-100%로 정규화하여 표시합니다.
        </div>
      </div>
    </div>
  );
};

export default FxRatesChart;
