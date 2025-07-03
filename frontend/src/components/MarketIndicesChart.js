import React, { useState } from 'react';

const MarketIndicesChart = ({ data, loading, error }) => {
  const [selectedIndex, setSelectedIndex] = useState('dow');

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

  // 지수 정보 매핑
  const indexInfo = {
    dow: { name: 'DOW', data: data.dow, color: '#1f77b4', key: 'dow' },
    sp500: { name: 'S&P 500', data: data.sp500, color: '#ff7f0e', key: 'sp500' },
    nasdaq: { name: 'NASDAQ', data: data.nasdaq, color: '#2ca02c', key: 'nasdaq' }
  };

  // 사용 가능한 지수들만 필터링
  const availableIndices = Object.keys(indexInfo).filter(key => {
    const info = indexInfo[key];
    return info.data && info.data.dates && info.data.closes;
  });

  if (availableIndices.length === 0) {
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

  // 현재 선택된 지수가 사용 가능한지 확인하고, 없으면 첫 번째 사용 가능한 지수로 변경
  const currentIndex = availableIndices.includes(selectedIndex) ? selectedIndex : availableIndices[0];
  const currentIndexInfo = indexInfo[currentIndex];

  // 차트 크기 설정
  const width = 800;
  const height = 300;
  const padding = 50;

  // 현재 지수의 최대/최소값 계산
  const currentValues = currentIndexInfo.data.closes || [];
  
  if (currentValues.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#666'
      }}>
        선택된 지수의 데이터가 없습니다.
      </div>
    );
  }

  const maxValue = Math.max(...currentValues);
  const minValue = Math.min(...currentValues);
  const valueRange = maxValue - minValue || 1;
  
  // 평균가격 계산
  const avgValue = currentValues.reduce((sum, value) => sum + value, 0) / currentValues.length;

  // 날짜 범위 계산
  const dates = currentIndexInfo.data.dates;
  const dateCount = dates.length;

  const xStep = (width - 2 * padding) / (dateCount - 1 || 1);
  const yScale = (value) => padding + ((maxValue - value) / valueRange) * (height - 2 * padding);
  
  // 평균선 y좌표
  const avgY = yScale(avgValue);

  return (
    <div style={{ 
      backgroundColor: '#ffffff',
      borderRadius: '8px',
      border: '1px solid #e0e0e0',
      padding: '20px',
      marginBottom: '8px'
    }}>
      
      {/* 지수 선택 버튼들 */}
      <div style={{ 
        marginBottom: '20px',
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap'
      }}>
        {Object.keys(indexInfo).map((key) => {
          const isAvailable = availableIndices.includes(key);
          const isSelected = currentIndex === key;
          // 모든 버튼 색상 EFC352
          const mainColor = '#EFC352';
          return (
            <button
              key={key}
              onClick={() => setSelectedIndex(key)}
              disabled={!isAvailable}
              style={{
                padding: '8px 16px',
                border: isSelected ? `2px solid ${mainColor}` : '1px solid #ddd',
                borderRadius: '6px',
                backgroundColor: isSelected ? `${mainColor}20` : (isAvailable ? '#ffffff' : '#f5f5f5'),
                color: isSelected ? mainColor : (isAvailable ? '#333' : '#999'),
                cursor: isAvailable ? 'pointer' : 'not-allowed',
                fontWeight: isSelected ? 'bold' : 'normal',
                fontSize: '14px',
                transition: 'all 0.2s ease'
              }}
            >
              {indexInfo[key].name}
            </button>
          );
        })}
      </div>
      
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
          
          {/* 선택된 지수의 라인 그리기 */}
          {(() => {
            // 평균선을 기준으로 위/아래 구간별로 색상을 다르게 표시
            const segments = [];
            for (let i = 0; i < currentValues.length - 1; i++) {
              const x1 = padding + i * xStep;
              const y1 = yScale(currentValues[i]);
              const x2 = padding + (i + 1) * xStep;
              const y2 = yScale(currentValues[i + 1]);
              
              const above1 = currentValues[i] >= avgValue;
              const above2 = currentValues[i + 1] >= avgValue;
              
              if (above1 === above2) {
                // 두 점이 모두 평균선 위 또는 아래에 있는 경우
                segments.push({ 
                  x1, y1, x2, y2, 
                  color: above1 ? '#ef4444' : '#3b82f6' // 빨간색 : 파란색
                });
              } else {
                // 평균선과 교차하는 경우
                const t = (avgValue - currentValues[i]) / (currentValues[i + 1] - currentValues[i]);
                const crossX = x1 + t * (x2 - x1);
                const crossY = avgY;
                
                segments.push({ 
                  x1, y1, 
                  x2: crossX, y2: crossY, 
                  color: above1 ? '#ef4444' : '#3b82f6'
                });
                segments.push({ 
                  x1: crossX, y1: crossY, 
                  x2, y2, 
                  color: above2 ? '#ef4444' : '#3b82f6'
                });
              }
            }

            return (
              <g>
                {/* 그라데이션 정의 */}
                <defs>
                  <linearGradient id="red-gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0.05" />
                  </linearGradient>
                  {/* blue-gradient: graph 선에서 진하고, average에서 연하게 반전 */}
                  <linearGradient id="blue-gradient" x1="0" y1="1" x2="0" y2="0">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.18" />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
                  </linearGradient>
                </defs>

                {/* 평균선 */}
                <line 
                  x1={padding} 
                  y1={avgY} 
                  x2={width - padding} 
                  y2={avgY} 
                  stroke="#888" 
                  strokeDasharray="4 2" 
                  strokeWidth="1.5" 
                />

                {/* 영역 채우기 (matplotlib fill_between 스타일) */}
                {(() => {
                  // 평균선과 교차점 보간
                  const aboveAreas = [];
                  const belowAreas = [];
                  let currentArea = [];
                  let currentType = null; // 'above' or 'below'
                  function pushArea(type, area) {
                    if (area.length > 1) {
                      (type === 'above' ? aboveAreas : belowAreas).push([...area]);
                    }
                  }
                  for (let i = 0; i < currentValues.length; i++) {
                    const x = padding + i * xStep;
                    const y = yScale(currentValues[i]);
                    const isAbove = currentValues[i] >= avgValue;
                    if (currentType === null) {
                      currentType = isAbove ? 'above' : 'below';
                      currentArea.push({ x, y, origIdx: i });
                    } else if ((isAbove && currentType === 'above') || (!isAbove && currentType === 'below')) {
                      currentArea.push({ x, y, origIdx: i });
                    } else {
                      // 평균선과 교차: 보간점 추가
                      const prevIdx = i - 1;
                      const x1 = padding + prevIdx * xStep;
                      const y1 = yScale(currentValues[prevIdx]);
                      const x2 = x;
                      const y2 = y;
                      const v1 = currentValues[prevIdx];
                      const v2 = currentValues[i];
                      const t = (avgValue - v1) / (v2 - v1);
                      const crossX = x1 + t * (x2 - x1);
                      const crossY = avgY;
                      currentArea.push({ x: crossX, y: crossY, origIdx: null });
                      pushArea(currentType, currentArea);
                      // 새 영역 시작
                      currentType = isAbove ? 'above' : 'below';
                      currentArea = [{ x: crossX, y: crossY, origIdx: null }, { x, y, origIdx: i }];
                    }
                  }
                  pushArea(currentType, currentArea);

                  // 각 영역을 polygon으로 만듦 (평균선까지 닫음)
                  const polygons = [];
                  aboveAreas.forEach(area => {
                    const points = [
                      { x: area[0].x, y: avgY },
                      ...area,
                      { x: area[area.length - 1].x, y: avgY }
                    ];
                    polygons.push(
                      <polygon
                        key={"above-" + area[0].x}
                        points={points.map(p => `${p.x},${p.y}`).join(' ')}
                        fill="url(#red-gradient)"
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
                        key={"below-" + area[0].x}
                        points={points.map(p => `${p.x},${p.y}`).join(' ')}
                        fill="url(#blue-gradient)"
                        stroke="none"
                        style={{ pointerEvents: 'none' }}
                      />
                    );
                  });
                  return polygons;
                })()}

                {/* 구간별 색상으로 라인 그리기 */}
                {segments.map((seg, i) => (
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
                
                {/* 기간 정보를 우상단에 표시 */}
                <text
                  x={width - padding - 10}
                  y={padding - 30}
                  textAnchor="end"
                  fontSize="13"
                  fill="#666"
                  fontWeight="medium"
                >
                  {dates[0]} - {dates[dates.length - 1]}
                </text>
              </g>
            );
          })()}
          
          {/* X축 날짜 레이블 (일부만) */}
          {dates.map((date, i) => {
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
        backgroundColor: 'rgba(229, 223, 209, 0.5)',
        borderRadius: '6px',
        fontSize: '14px',
        color: '#555'
      }}>
        <div style={{ marginBottom: '8px' }}>
          <strong>{currentIndexInfo.name} 정보:</strong>
        </div>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' }}>
          <span><strong>최고가:</strong> {maxValue.toLocaleString()}</span>
          <span><strong>최저가:</strong> {minValue.toLocaleString()}</span>
          <span><strong>평균가:</strong> {avgValue.toFixed(0).toLocaleString()}</span>
          <span><strong>최신가:</strong> {currentValues[currentValues.length - 1]?.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
};

export default MarketIndicesChart;
