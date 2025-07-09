import React from "react";

// 6개월치 Apple 주가 임의 데이터 (월별 종가) 그래프 샘플 컴포넌트
function PipelineGraphSample() {
  const data = [
    { month: '1월', price: 185 },
    { month: '2월', price: 192 },
    { month: '3월', price: 188 },
    { month: '4월', price: 200 },
    { month: '5월', price: 210 },
    { month: '6월', price: 205 }
  ];
  const maxValue = Math.max(...data.map(d => d.price));
  const minValue = Math.min(...data.map(d => d.price));
  const avgValue = data.reduce((sum, d) => sum + d.price, 0) / data.length;
  const width = 320;
  const height = 120;
  const padding = 32;
  const yAxisWidth = 32;
  const xStep = (width - 2 * padding - yAxisWidth) / (data.length - 1);
  const yScale = price => padding + ((maxValue - price) / (maxValue - minValue || 1)) * (height - 2 * padding);
  const avgY = yScale(avgValue);
  const segments = [];
  for (let i = 0; i < data.length - 1; i++) {
    const x1 = padding + yAxisWidth + i * xStep;
    const y1 = yScale(data[i].price);
    const x2 = padding + yAxisWidth + (i + 1) * xStep;
    const y2 = yScale(data[i + 1].price);
    const above1 = data[i].price >= avgValue;
    const above2 = data[i + 1].price >= avgValue;
    if (above1 === above2) {
      segments.push({ x1, y1, x2, y2, color: above1 ? '#ef4444' : '#3b82f6' });
    } else {
      const t = (avgValue - data[i].price) / (data[i + 1].price - data[i].price);
      const crossX = x1 + t * (x2 - x1);
      const crossY = avgY;
      segments.push({ x1, y1, x2: crossX, y2: crossY, color: above1 ? '#ef4444' : '#3b82f6' });
      segments.push({ x1: crossX, y1: crossY, x2, y2, color: above2 ? '#ef4444' : '#3b82f6' });
    }
  }
  const yTicks = [];
  const tickStep = 5;
  for (let v = Math.ceil(minValue / tickStep) * tickStep; v <= maxValue; v += tickStep) {
    yTicks.push(v);
  }
  return (
    <div className="pipeline-graph-sample">
      <svg width={width} height={height} className="line-graph-svg">
        <line x1={padding + yAxisWidth} y1={padding} x2={padding + yAxisWidth} y2={height - padding} stroke="#bbb" strokeWidth="1" />
        <line x1={padding + yAxisWidth} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#bbb" strokeWidth="1" />
        {yTicks.map((v, i) => {
          const y = yScale(v);
          return (
            <g key={v}>
              <line
                x1={padding + yAxisWidth}
                y1={y}
                x2={width - padding}
                y2={y}
                stroke="#ddd"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
              <text
                x={padding + yAxisWidth - 6}
                y={y + 4}
                textAnchor="end"
                fontSize="11"
                fill="#888"
              >
                {v}
              </text>
            </g>
          );
        })}
        <line x1={padding + yAxisWidth} y1={avgY} x2={width - padding} y2={avgY} stroke="#888" strokeDasharray="4 2" strokeWidth="1.5" />
        <text x={width - padding + 4} y={avgY + 4} fontSize="12" fill="#888">평균 {avgValue.toFixed(1)}</text>
        {segments.map((seg, i) => (
          <line
            key={i}
            x1={seg.x1}
            y1={seg.y1}
            x2={seg.x2}
            y2={seg.y2}
            stroke={seg.color}
            strokeWidth="2.5"
          />
        ))}
        {data.map((d, i) => (
          <text
            key={d.month}
            x={padding + yAxisWidth + i * xStep}
            y={height - padding + 18}
            textAnchor="middle"
            fontSize="12"
            fill="#555"
          >
            {d.month}
          </text>
        ))}
      </svg>
    </div>
  );
}

export default PipelineGraphSample;
