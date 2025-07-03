import React, { useState } from 'react';

const TreasuryYieldsChart = ({ data, loading, error }) => {
  const [selectedYield, setSelectedYield] = useState('us_2y');

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

  // 선택된 금리 데이터
  const yieldInfo = {
    us_2y: {
      name: '미국 국채 2년물',
      color: '#e74c3c',
      data: data.us_2y
    },
    us_10y: {
      name: '미국 국채 10년물',
      color: '#3498db',
      data: data.us_10y
    }
  };
  const currentYield = yieldInfo[selectedYield];
  const currentValues = currentYield.data.filter(val => val !== null && val !== undefined);
  const allYields = currentYield.data.filter(val => val !== null && val !== undefined);
  if (allYields.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #e9ecef'
      }}>
        선택된 기간의 국채 금리 데이터가 없습니다.
      </div>
    );
  }
  const maxValue = Math.max(...allYields);
  const minValue = Math.min(...allYields);
  const valueRange = maxValue - minValue || 1;
  const avgValue = allYields.reduce((sum, v) => sum + v, 0) / allYields.length;
  const dateCount = data.dates.length;
  const xStep = (width - 2 * padding) / (dateCount - 1 || 1);
  const yScale = (value) => {
    if (value === null || value === undefined) return null;
    return padding + ((maxValue - value) / valueRange) * (height - 2 * padding);
  };

  // 기준선: 첫 번째 값(그림과 동일)
  const baseValue = currentYield.data.find(v => v !== null && v !== undefined);
  const baseY = yScale(baseValue);

  // fill_between 영역 polygon 생성 (기준선 기준)
  const createFillPolygons = () => {
    const aboveAreas = [];
    const belowAreas = [];
    let currentArea = [];
    let currentType = null;
    function pushArea(type, area) {
      if (area.length > 1) {
        (type === 'above' ? aboveAreas : belowAreas).push([...area]);
      }
    }
    for (let i = 0; i < currentYield.data.length; i++) {
      const val = currentYield.data[i];
      if (val === null || val === undefined) continue;
      const x = padding + i * xStep;
      const y = yScale(val);
      const isAbove = val >= baseValue;
      if (currentType === null) {
        currentType = isAbove ? 'above' : 'below';
        currentArea.push({ x, y });
      } else if ((isAbove && currentType === 'above') || (!isAbove && currentType === 'below')) {
        currentArea.push({ x, y });
      } else {
        // 기준선과 교차: 보간점 추가
        const prevIdx = i - 1;
        const prevVal = currentYield.data[prevIdx];
        const x1 = padding + prevIdx * xStep;
        const y1 = yScale(prevVal);
        const x2 = x;
        const y2 = y;
        const t = (baseValue - prevVal) / (val - prevVal);
        const crossX = x1 + t * (x2 - x1);
        const crossY = baseY;
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
        { x: area[0].x, y: baseY },
        ...area,
        { x: area[area.length - 1].x, y: baseY }
      ];
      polygons.push(
        <polygon
          key={'above-' + area[0].x}
          points={points.map(p => `${p.x},${p.y}`).join(' ')}
          fill="url(#red-gradient-treasury)"
          stroke="none"
          style={{ pointerEvents: 'none' }}
        />
      );
    });
    belowAreas.forEach(area => {
      const points = [
        { x: area[0].x, y: baseY },
        ...area,
        { x: area[area.length - 1].x, y: baseY }
      ];
      polygons.push(
        <polygon
          key={'below-' + area[0].x}
          points={points.map(p => `${p.x},${p.y}`).join(' ')}
          fill="url(#blue-gradient-treasury)"
          stroke="none"
          style={{ pointerEvents: 'none' }}
        />
      );
    });
    return polygons;
  };

  // 구간별 색상 라인(기준선 기준)
  const createSegments = () => {
    const segments = [];
    for (let i = 0; i < currentYield.data.length - 1; i++) {
      const v1 = currentYield.data[i];
      const v2 = currentYield.data[i + 1];
      if (v1 === null || v1 === undefined || v2 === null || v2 === undefined) continue;
      const x1 = padding + i * xStep;
      const y1 = yScale(v1);
      const x2 = padding + (i + 1) * xStep;
      const y2 = yScale(v2);
      const above1 = v1 >= baseValue;
      const above2 = v2 >= baseValue;
      if (above1 === above2) {
        segments.push({ x1, y1, x2, y2, color: above1 ? '#ef4444' : '#3b82f6' });
      } else {
        // 기준선과 교차
        const t = (baseValue - v1) / (v2 - v1);
        const crossX = x1 + t * (x2 - x1);
        const crossY = baseY;
        segments.push({ x1, y1, x2: crossX, y2: crossY, color: above1 ? '#ef4444' : '#3b82f6' });
        segments.push({ x1: crossX, y1: crossY, x2, y2, color: above2 ? '#ef4444' : '#3b82f6' });
      }
    }
    return segments;
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
    for (let i = 0; i < currentYield.data.length; i++) {
      const val = currentYield.data[i];
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
        const prevVal = currentYield.data[prevIdx];
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

  // 라인 포인트 생성 (null 값 제외)
  const createPoints = (yieldArr) => {
    const points = [];
    for (let i = 0; i < yieldArr.length; i++) {
      if (yieldArr[i] !== null && yieldArr[i] !== undefined) {
        const x = padding + i * xStep;
        const y = yScale(yieldArr[i]);
        if (y !== null) points.push(`${x},${y}`);
      }
    }
    return points.join(' ');
  };

  // MarketIndicesChart 스타일의 SVG 차트
  return (
    <div style={{ 
      backgroundColor: '#ffffff',
      borderRadius: '8px',
      border: '1px solid #e0e0e0',
      padding: '20px',
      marginBottom: '8px'
    }}>
      {/* 버튼 row - MarketIndicesChart와 동일 스타일 */}
      <div style={{ 
        marginBottom: '20px',
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap',
      }}>
        {Object.keys(yieldInfo).map((key) => {
          const isSelected = selectedYield === key;
          const mainColor = '#EFC352';
          return (
            <button
              key={key}
              onClick={() => setSelectedYield(key)}
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
              {yieldInfo[key].name}
            </button>
          );
        })}
      </div>
      <div style={{ overflowX: 'auto' }}>
        <svg width={width} height={height} style={{ minWidth: '800px' }}>
          {/* 배경 격자 */}
          <defs>
            <pattern id="grid-treasury" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f0f0f0" strokeWidth="1"/>
            </pattern>
            {/* 그라데이션 정의 */}
            <linearGradient id="red-gradient-treasury" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.05" />
            </linearGradient>
            <linearGradient id="blue-gradient-treasury" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
            </linearGradient>
          </defs>
          <rect width={width} height={height} fill="url(#grid-treasury)" />
          {/* Y축 */}
          <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#ccc" strokeWidth="1" />
          {/* X축 */}
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#ccc" strokeWidth="1" />
          {/* Y축 눈금 및 레이블 (내림차순) */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const value = maxValue - ratio * valueRange;
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
          {/* 기준선 (굵은 점선, 평균 금리 기준, MarketIndicesChart와 동일 스타일) */}
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
          {(() => {
            const segments = [];
            for (let i = 0; i < currentYield.data.length - 1; i++) {
              const v1 = currentYield.data[i];
              const v2 = currentYield.data[i + 1];
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
            return segments.map((seg, i) => (
              <line
                key={i}
                x1={seg.x1}
                y1={seg.y1}
                x2={seg.x2}
                y2={seg.y2}
                stroke={seg.color}
                strokeWidth="3"
              />
            ));
          })()}
          {/* 기간 정보 우상단 표시 */}
          <text
            x={width - padding - 10}
            y={padding - 30}
            textAnchor="end"
            fontSize="13"
            fill="#666"
            fontWeight="medium"
          >
            {data.dates[0]} - {data.dates[data.dates.length - 1]}
          </text>
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
      {/* 간단한 요약 - MarketIndicesChart와 동일 스타일 */}
      <div style={{ 
        marginTop: '16px',
        padding: '12px',
        backgroundColor: 'rgba(229, 223, 209, 0.5)',
        borderRadius: '6px',
        fontSize: '14px',
        color: '#555'
      }}>
        <div style={{ marginBottom: '8px' }}>
          <strong>{currentYield.name} 정보:</strong>
        </div>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' }}>
          <span><strong>최고 금리:</strong> {maxValue.toFixed(2)}%</span>
          <span><strong>최저 금리:</strong> {minValue.toFixed(2)}%</span>
          <span><strong>평균 금리:</strong> {avgValue.toFixed(2)}%</span>
          <span><strong>최근 금리:</strong> {currentYield.data[currentYield.data.length - 1]?.toFixed(2)}%</span>
        </div>
      </div>
    </div>
  );
};

export default TreasuryYieldsChart;
