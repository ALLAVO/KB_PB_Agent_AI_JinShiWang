import React, { useState } from 'react';

const FxRatesChart = ({ data, loading, error }) => {
  const [selectedFx, setSelectedFx] = useState('usd_krw');

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

  // 버튼 정보
  const fxInfo = {
    usd_krw: {
      name: 'USD/KRW',
      color: '#e67e22',
      values: data.usd_krw,
      min: Math.min(...data.usd_krw.filter(v => v !== null && v !== undefined)),
      max: Math.max(...data.usd_krw.filter(v => v !== null && v !== undefined)),
      format: v => v?.toLocaleString(),
      decimals: 0
    },
    eur_usd: {
      name: 'EUR/USD',
      color: '#9b59b6',
      values: data.eur_usd,
      min: Math.min(...data.eur_usd.filter(v => v !== null && v !== undefined)),
      max: Math.max(...data.eur_usd.filter(v => v !== null && v !== undefined)),
      format: v => v?.toFixed(4),
      decimals: 4
    }
  };

  const currentFx = fxInfo[selectedFx];
  const values = currentFx.values.filter(v => v !== null && v !== undefined);
  if (values.length === 0) {
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

  const min = currentFx.min;
  const max = currentFx.max;
  const valueRange = max - min || 1;
  const avgValue = values.reduce((sum, v) => sum + v, 0) / values.length;
  const dateCount = data.dates.length;
  const xStep = (width - 2 * padding) / (dateCount - 1 || 1);
  const yScale = (value) => {
    if (value === null || value === undefined) return null;
    return padding + ((max - value) / valueRange) * (height - 2 * padding);
  };

  // fill_between 영역 polygon 생성 (평균선 기준)
  const avgY = yScale(avgValue);
  const createAvgFillPolygons = () => {
    const aboveAreas = [];
    const belowAreas = [];
    let currentArea = [];
    let currentType = null;
    function pushArea(type, area) {
      if (area.length > 1) {
        (type === 'above' ? aboveAreas : belowAreas).push([...area]);
      }
    }
    for (let i = 0; i < currentFx.values.length; i++) {
      const val = currentFx.values[i];
      if (val === null || val === undefined) continue;
      const x = padding + i * xStep;
      const y = yScale(val);
      const isAbove = val >= avgValue;
      if (currentType === null) {
        currentType = isAbove ? 'above' : 'below';
        currentArea.push({ x, y });
      } else if ((isAbove && currentType === 'above') || (!isAbove && currentType === 'below')) {
        currentArea.push({ x, y });
      } else {
        // 평균선과 교차: 보간점 추가
        const prevIdx = i - 1;
        const prevVal = currentFx.values[prevIdx];
        const x1 = padding + prevIdx * xStep;
        const y1 = yScale(prevVal);
        const x2 = x;
        const y2 = y;
        const t = (avgValue - prevVal) / (val - prevVal);
        const crossX = x1 + t * (x2 - x1);
        const crossY = avgY;
        currentArea.push({ x: crossX, y: crossY });
        pushArea(currentType, currentArea);
        currentType = isAbove ? 'above' : 'below';
        currentArea = [{ x: crossX, y: crossY }, { x, y }];
      }
    }
    pushArea(currentType, currentArea);
    // polygon 생성
    const polygons = [];
    aboveAreas.forEach(area => {
      const points = [
        { x: area[0].x, y: avgY },
        ...area,
        { x: area[area.length - 1].x, y: avgY }
      ];
      polygons.push(
        <polygon
          key={'avg-above-' + area[0].x}
          points={points.map(p => `${p.x},${p.y}`).join(' ')}
          fill="url(#red-gradient-treasury)"
          stroke="none"
          style={{ pointerEvents: 'none' }}
        />
      );
    });
    belowAreas.forEach(area => {
      const points = [
        { x: area[0].x, y: avgY },
        ...area,
        { x: area[area.length - 1].x, y: avgY }
      ];
      polygons.push(
        <polygon
          key={'avg-below-' + area[0].x}
          points={points.map(p => `${p.x},${p.y}`).join(' ')}
          fill="url(#blue-gradient-treasury)"
          stroke="none"
          style={{ pointerEvents: 'none' }}
        />
      );
    });
    return polygons;
  };

  // 구간별 색상 라인(평균선 기준)
  const createSegments = () => {
    const segments = [];
    for (let i = 0; i < currentFx.values.length - 1; i++) {
      const v1 = currentFx.values[i];
      const v2 = currentFx.values[i + 1];
      if (v1 === null || v1 === undefined || v2 === null || v2 === undefined) continue;
      const x1 = padding + i * xStep;
      const y1 = yScale(v1);
      const x2 = padding + (i + 1) * xStep;
      const y2 = yScale(v2);
      const above1 = v1 >= avgValue;
      const above2 = v2 >= avgValue;
      if (above1 === above2) {
        segments.push({ x1, y1, x2, y2, color: above1 ? '#ef4444' : '#3b82f6' });
      } else {
        // 평균선과 교차
        const t = (avgValue - v1) / (v2 - v1);
        const crossX = x1 + t * (x2 - x1);
        const crossY = avgY;
        segments.push({ x1, y1, x2: crossX, y2: crossY, color: above1 ? '#ef4444' : '#3b82f6' });
        segments.push({ x1: crossX, y1: crossY, x2, y2, color: above2 ? '#ef4444' : '#3b82f6' });
      }
    }
    return segments;
  };

  // 라인 포인트 생성 (null 값 제외)
  const createPoints = () => {
    const points = [];
    for (let i = 0; i < currentFx.values.length; i++) {
      const v = currentFx.values[i];
      if (v !== null && v !== undefined) {
        const x = padding + i * xStep;
        const y = yScale(v);
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
      marginBottom: '8px'
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
      {/* 버튼 row */}
      <div style={{ 
        marginBottom: '20px',
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap',
      }}>
        {Object.keys(fxInfo).map((key) => {
          const isSelected = selectedFx === key;
          const mainColor = '#EFC352';
          return (
            <button
              key={key}
              onClick={() => setSelectedFx(key)}
              style={{
                padding: '8px 16px',
                border: isSelected ? `2px solid ${mainColor}` : '1px solid #ddd',
                borderRadius: '6px',
                backgroundColor: isSelected ? `${mainColor}20` : '#fff',
                color: isSelected ? mainColor : '#333',
                cursor: 'pointer',
                fontWeight: isSelected ? 'bold' : 'normal',
                fontSize: '14px',
                transition: 'all 0.2s ease'
              }}
            >
              {fxInfo[key].name}
            </button>
          );
        })}
      </div>
      <div style={{ overflowX: 'auto' }}>
        <svg width={width} height={height} style={{ minWidth: '800px' }}>
          {/* 배경 격자 및 그라데이션 정의 */}
          <defs>
            <pattern id="grid-fx" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f0f0f0" strokeWidth="1"/>
            </pattern>
            <linearGradient id="red-gradient-treasury" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.05" />
            </linearGradient>
            <linearGradient id="blue-gradient-treasury" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
            </linearGradient>
          </defs>
          <rect width={width} height={height} fill="url(#grid-fx)" />
          {/* Y축 */}
          <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#ccc" strokeWidth="1" />
          {/* X축 */}
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#ccc" strokeWidth="1" />
          {/* Y축 눈금 및 레이블 (내림차순) */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const value = max - ratio * valueRange;
            const y = padding + ratio * (height - 2 * padding);
            return (
              <g key={ratio}>
                <line x1={padding - 5} y1={y} x2={padding} y2={y} stroke="#ccc" strokeWidth="1" />
                <text x={padding - 10} y={y + 4} textAnchor="end" fontSize="11" fill="#666">
                  {currentFx.format(value)}
                </text>
              </g>
            );
          })}
          {/* 평균선 (기준선) */}
          <line 
            x1={padding} 
            y1={avgY} 
            x2={width - padding} 
            y2={avgY} 
            stroke="#888" 
            strokeDasharray="4 2" 
            strokeWidth="1.5" 
          />
          {/* fill_between 영역 (평균선 기준) */}
          {createAvgFillPolygons()}
          {/* 구간별 색상 라인 (평균선 기준) */}
          {createSegments().map((seg, i) => (
            <line
              key={i}
              x1={seg.x1}
              y1={seg.y1}
              x2={seg.x2}
              y2={seg.y2}
              stroke={seg.color}
              strokeWidth="3"
            />
          ))}
          {/* 환율 라인 */}
          <polyline
            fill="none"
            stroke={currentFx.color}
            strokeWidth="3"
            points={createPoints()}
          />
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
      {/* 요약 정보 - TreasuryYieldsChart와 동일 스타일 */}
      <div style={{ 
        marginTop: '16px',
        padding: '12px',
        backgroundColor: 'rgba(229, 223, 209, 0.5)',
        borderRadius: '6px',
        fontSize: '14px',
        color: '#555'
      }}>
        <div style={{ marginBottom: '8px' }}>
          <strong>6개월 기간:</strong> {data.dates[0]} ~ {data.dates[data.dates.length - 1]}
        </div>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' }}>
          <span><strong>최고값:</strong> {currentFx.format(max)}</span>
          <span><strong>최저값:</strong> {currentFx.format(min)}</span>
          <span><strong>평균값:</strong> {currentFx.format(avgValue)}</span>
          <span><strong>최근값:</strong> {currentFx.format(currentFx.values[currentFx.values.length - 1])}</span>
        </div>
      </div>
    </div>
  );
};

export default FxRatesChart;
