import React from 'react';

const PortfolioChart = ({ chartData, onIndustryClick }) => {
  const createDonutChart = (data, title) => {
    if (!data || data.length === 0) {
      return (
        <div className="chart-placeholder">
          <p>데이터가 없습니다</p>
        </div>
      );
    }

    // 색상 팔레트
    const colors = [
      '#F5E6A3', '#8B7355', '#D4B96A', '#7BA05B', '#C4756E',
      '#E5DFD1', '#FAF2D1', '#E5D084', '#6D5A42', '#FEFCF7'
    ];

    const total = data.reduce((sum, item) => sum + item.percentage, 0);
    let currentAngle = 0;

    const radius = 80;
    const centerX = 100;
    const centerY = 100;

    const createArcPath = (startAngle, endAngle, outerRadius, innerRadius = 40) => {
      const start = polarToCartesian(centerX, centerY, outerRadius, endAngle);
      const end = polarToCartesian(centerX, centerY, outerRadius, startAngle);
      const innerStart = polarToCartesian(centerX, centerY, innerRadius, endAngle);
      const innerEnd = polarToCartesian(centerX, centerY, innerRadius, startAngle);

      const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

      return [
        "M", start.x, start.y,
        "A", outerRadius, outerRadius, 0, largeArcFlag, 0, end.x, end.y,
        "L", innerEnd.x, innerEnd.y,
        "A", innerRadius, innerRadius, 0, largeArcFlag, 1, innerStart.x, innerStart.y,
        "Z"
      ].join(" ");
    };

    const polarToCartesian = (centerX, centerY, radius, angleInDegrees) => {
      const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
      return {
        x: centerX + (radius * Math.cos(angleInRadians)),
        y: centerY + (radius * Math.sin(angleInRadians))
      };
    };

    return (
      <div className="donut-chart-container">
        <h4 className="chart-title">{title}</h4>
        <div className="chart-content">
          <svg width="200" height="200" viewBox="0 0 200 200" className="donut-chart">
            {data.map((item, index) => {
              const angle = (item.percentage / 100) * 360;
              const path = createArcPath(currentAngle, currentAngle + angle, radius);
              const textAngle = currentAngle + angle / 2;
              const textRadius = 60;
              const textPos = polarToCartesian(centerX, centerY, textRadius, textAngle);
              
              currentAngle += angle;

              return (
                <g key={index} className="chart-segment">
                  <path
                    d={path}
                    fill={colors[index % colors.length]}
                    stroke="#fff"
                    strokeWidth="2"
                    className="chart-arc"
                  />
                  {item.percentage > 5 && (
                    <text
                      x={textPos.x}
                      y={textPos.y}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fontSize="10"
                      fill="#333"
                      fontWeight="bold"
                    >
                      {item.percentage}%
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
          <div className="chart-legend">
            {data.map((item, index) => (
              <div 
                key={index} 
                className="legend-item"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '4px 0'
                }}
              >
                <div 
                  className="legend-color" 
                  style={{ backgroundColor: colors[index % colors.length] }}
                ></div>
                <span className="legend-label">{item.sector}</span>
                <span className="legend-value">{item.percentage}%</span>
                {onIndustryClick && (
                  <button
                    onClick={() => onIndustryClick(item.sector)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '2px',
                      marginLeft: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                    title={`${item.sector} 산업 분석으로 이동`}
                  >
                    <img 
                      src={require('../../assets/arrow.png')} 
                      alt="arrow" 
                      style={{ 
                        width: '12px', 
                        height: '12px',
                        opacity: 0.7
                      }} 
                    />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  if (!chartData) {
    return <div>차트 데이터를 불러오고 있습니다...</div>;
  }

  const { client_name, risk_profile_info, client_portfolio, recommended_portfolio } = chartData;

  return (
    <>
      <div className="portfolio-charts-container">
        <div className="chart-column" style={{ marginLeft: '40px', width: '380px' }}>
          {createDonutChart(client_portfolio, `${client_name}님 포트폴리오`)}
        </div>
        <div className="chart-column" style={{ marginRight: '40px', width: '380px' }}>
          {createDonutChart(
            recommended_portfolio, 
            `${risk_profile_info?.korean_name || risk_profile_info?.label || '추천'} 위험군 포트폴리오`
          )}
        </div>
      </div>
    </>
  );
};

export default PortfolioChart;
