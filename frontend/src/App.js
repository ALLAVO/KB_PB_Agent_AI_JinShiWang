import React, { useState } from "react";
import "./App.css";
import kblogo from "./kblogo";
import { getWeeksOfMonth } from "./weekUtils";
import sendIcon from "./assets/send.png";
import cloud1 from "./assets/cloud1.png";
import cloud2 from "./assets/cloud2.png";
import cloud3 from "./assets/cloud3.png";
import titlecloud from "./assets/titlecloud.png";

function StackIconDecoration() {
  return (
    <img
      src={require('./assets/stack.png')}
      alt="stack"
      style={{
        position: 'absolute',
        right: '32px',
        top: '32px',
        width: 25,
        height: 25,
        zIndex: 2
      }}
    />
  );
}

function CloudDecorations() {
  return (
    <>
      <img src={cloud1} alt="cloud1" style={{ position: 'absolute', left: '0px', top: '80px', width: '50%', opacity: 1.0, pointerEvents: 'none', zIndex: 0 }} />
      <img src={cloud2} alt="cloud2" style={{ position: 'absolute', right: '0px', top: '38%', width: '50%', opacity: 1.0, pointerEvents: 'none', zIndex: 0 }} />
      <img src={cloud3} alt="cloud3" style={{ position: 'absolute', left: '0px', bottom: '60px', width: '50%', opacity: 1.0, pointerEvents: 'none', zIndex: 0 }} />
    </>
  );
}

function Sidebar({ userName, menu, subMenu, onMenuClick, onSubMenuClick, selectedMenu, selectedSubMenu, year, setYear, month, setMonth, period, onPeriodChange }) {
  // 연도/월 옵션 생성
  const yearOptions = Array.from({ length: 2025 - 1990 + 1 }, (_, i) => 1990 + i);
  const monthOptions = Array.from({ length: 12 }, (_, i) => i + 1);
  // 주차 옵션 생성 (선택된 연/월 기준)
  const weekOptions = getWeeksOfMonth(year, month).map(({ week, start, end }) => {
    const startStr = `${String(start.getMonth() + 1).padStart(2, '0')}.${String(start.getDate()).padStart(2, '0')}`;
    const endStr = `${String(end.getMonth() + 1).padStart(2, '0')}.${String(end.getDate()).padStart(2, '0')}`;
    return {
      value: `${startStr} - ${endStr} (${week}주차)`,
      label: `${startStr} - ${endStr} (${week}주차)`
    };
  });

  return (
    <div className="sidebar">
      <div className="sidebar-user">
        <div className="sidebar-user-badge">
          <img src={kblogo} alt="KB로고" className="sidebar-user-logo" />
          <span className="sidebar-user-name">{userName}</span>
        </div>
      </div>
      <div className="sidebar-menu">
        {menu.map((m) => (
          <div key={m} className={`sidebar-menu-item${selectedMenu === m ? " selected" : ""}`} onClick={() => onMenuClick(m)}>
            {m}
            {m === "진시황의 혜안" && selectedMenu === m && (
              <div className="sidebar-submenu">
                {subMenu.map((s) => (
                  <div key={s} className={`sidebar-submenu-item${selectedSubMenu === s ? " selected" : ""}`} onClick={() => onSubMenuClick(s)}>
                    {s}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="sidebar-yearmonth">
        <select 
          value={year} 
          onChange={e => setYear(Number(e.target.value))} 
          className="sidebar-period-select"
        >
          {yearOptions.map(y => <option key={y} value={y}>{y}년</option>)}
        </select>
        <select 
          value={month} 
          onChange={e => setMonth(Number(e.target.value))} 
          className="sidebar-period-select"
        >
          {monthOptions.map(m => <option key={m} value={m}>{m}월</option>)}
        </select>
      </div>
      <div className="sidebar-period">
        <select value={period} onChange={e => onPeriodChange(e.target.value)} className="sidebar-period-select">
          {weekOptions.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
    </div>
  );
}

function ChatPanel() {
  const [input, setInput] = useState("");
  // textarea 높이 자동 조절
  const textareaRef = React.useRef(null);
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [input]);
  return (
    <div className="chat-panel" style={{position:'relative'}}>
      <StackIconDecoration />
      <div className="chat-title-row" style={{display:'flex',alignItems:'center',justifyContent:'space-between',paddingRight:48}}>
        <div className="chat-title" style={{ color: '#302A24' }}>진시황과의 상담</div>
      </div>
      <div className="chat-messages">
        <CloudDecorations />
        {/* 채팅 메시지 영역 */}
      </div>
      <div className="chat-input-row">
        <div className="chat-input-bg">
          <textarea
            ref={textareaRef}
            className="chat-input"
            placeholder="진시황에게 질문하세요..."
            value={input}
            onChange={e => setInput(e.target.value)}
            rows={1}
          />
        </div>
        <button className="chat-send-btn" disabled>
          <img src={sendIcon} alt="send" style={{width:25,height:25,opacity:0.7}} />
        </button>
      </div>
    </div>
  );
}

function CustomerPipeline({ year, month, weekStr }) {
  const chartData = '고객 차트 예시';
  const tableData = [
    { 이름: '홍길동', 등급: 'Gold', 최근방문: '2025-06-01' },
    { 이름: '김철수', 등급: 'Silver', 최근방문: '2025-06-03' }
  ];
  const textSummary = `${year}년 ${month}월 ${weekStr} 고객 데이터 분석 요약입니다.`;
  return (
    <div>
      <div className="pipeline-title">
        <img src={titlecloud} alt="cloud" />고객 Pipeline
      </div>
      <div className="pipeline-graph">{chartData}</div>
      <table className="pipeline-table">
        <thead>
          <tr>{Object.keys(tableData[0]).map((key) => <th key={key}>{key}</th>)}</tr>
        </thead>
        <tbody>
          {tableData.map((row, idx) => (
            <tr key={idx}>{Object.values(row).map((val, i) => <td key={i}>{val}</td>)}</tr>
          ))}
        </tbody>
      </table>
      <div className="pipeline-text">{textSummary}</div>
    </div>
  );
}

function MarketPipeline({ year, month, weekStr }) {
  const chartData = '시장 차트 예시';
  const tableData = [
    { 지수: 'KOSPI', 값: 2650, 변동: '+1.2%' },
    { 지수: 'KOSDAQ', 값: 900, 변동: '-0.5%' }
  ];
  const textSummary = `${year}년 ${month}월 ${weekStr} 시장 데이터 분석 요약입니다.`;
  return (
    <div>
      <div className="pipeline-title">
        <img src={titlecloud} alt="cloud" />증시 지표
      </div>
      <div className="pipeline-graph">{chartData}</div>
      <table className="pipeline-table">
        <thead>
          <tr>{Object.keys(tableData[0]).map((key) => <th key={key}>{key}</th>)}</tr>
        </thead>
        <tbody>
          {tableData.map((row, idx) => (
            <tr key={idx}>{Object.values(row).map((val, i) => <td key={i}>{val}</td>)}</tr>
          ))}
        </tbody>
      </table>
      <div className="pipeline-text">{textSummary}</div>
    </div>
  );
}

function IndustryPipeline({ year, month, weekStr }) {
  const chartData = '산업 차트 예시';
  const tableData = [
    { 산업: 'IT', 성장률: '5.2%' },
    { 산업: '바이오', 성장률: '3.1%' }
  ];
  const textSummary = `${year}년 ${month}월 ${weekStr} 산업 데이터 분석 요약입니다.`;
  return (
    <div>
      <div className="pipeline-title">
        <img src={titlecloud} alt="cloud" />산업 Pipeline
      </div>
      <div className="pipeline-graph">{chartData}</div>
      <table className="pipeline-table">
        <thead>
          <tr>{Object.keys(tableData[0]).map((key) => <th key={key}>{key}</th>)}</tr>
        </thead>
        <tbody>
          {tableData.map((row, idx) => (
            <tr key={idx}>{Object.values(row).map((val, i) => <td key={i}>{val}</td>)}</tr>
          ))}
        </tbody>
      </table>
      <div className="pipeline-text">{textSummary}</div>
    </div>
  );
}

function CompanyPipeline({ year, month, weekStr }) {
  const chartData = '기업 차트 예시';
  const tableData = [
    { 기업명: '삼성전자', 시가총액: '500조', PER: 12.3 },
    { 기업명: '네이버', 시가총액: '60조', PER: 35.1 }
  ];
  const textSummary = `${year}년 ${month}월 ${weekStr} 기업 데이터 분석 요약입니다.`;
  return (
    <div>
      <div className="pipeline-title">
        <img src={titlecloud} alt="cloud" />기업 Pipeline
      </div>
      <div className="pipeline-graph">{chartData}</div>
      <table className="pipeline-table">
        <thead>
          <tr>{Object.keys(tableData[0]).map((key) => <th key={key}>{key}</th>)}</tr>
        </thead>
        <tbody>
          {tableData.map((row, idx) => (
            <tr key={idx}>{Object.values(row).map((val, i) => <td key={i}>{val}</td>)}</tr>
          ))}
        </tbody>
      </table>
      <div className="pipeline-text">{textSummary}</div>
    </div>
  );
}

function PipelinePanel({ name, year, month, weekStr }) {
  if (name === 'customer') return <CustomerPipeline year={year} month={month} weekStr={weekStr} />;
  if (name === 'market') return <MarketPipeline year={year} month={month} weekStr={weekStr} />;
  if (name === 'industry') return <IndustryPipeline year={year} month={month} weekStr={weekStr} />;
  if (name === 'company') return <CompanyPipeline year={year} month={month} weekStr={weekStr} />;
  return null;
}

function MainPanel({ year, month, period, selectedMenu, selectedSubMenu }) {
  // 주차 정보 추출 (예: "(1주차)")
  const weekMatch = period.match(/\((\d+주차)\)/);
  const weekStr = weekMatch ? weekMatch[1] : "";

  // 메뉴/서브메뉴에 따라 보여줄 pipeline 결정
  let pipelineName = null;
  if (selectedMenu === "고객 관리") {
    pipelineName = "customer";
  } else if (selectedMenu === "진시황의 혜안") {
    if (selectedSubMenu === "시황") pipelineName = "market";
    else if (selectedSubMenu === "산업") pipelineName = "industry";
    else if (selectedSubMenu === "기업") pipelineName = "company";
  }

  return (
    <div className="main-panel">
      <div className="main-title">[{year}년 {month}월 {weekStr}] 시황 리포트</div>
      <div className="main-placeholder" style={{marginTop: '48px'}}>
        {pipelineName && (
          <PipelinePanel name={pipelineName} year={year} month={month} weekStr={weekStr} />
        )}
      </div>
    </div>
  );
}

function App() {
  const [selectedMenu, setSelectedMenu] = useState("진시황의 혜안");
  const [selectedSubMenu, setSelectedSubMenu] = useState("시황");
  const [year, setYear] = useState(2025);
  const [month, setMonth] = useState(6);
  const [period, setPeriod] = useState("06.01 - 06.07 (1주차)");

  return (
    <div className="app-layout">
      <Sidebar
        userName="김PB"
        menu={["진시황의 혜안", "고객 관리"]}
        subMenu={["시황", "산업", "기업"]}
        selectedMenu={selectedMenu}
        selectedSubMenu={selectedSubMenu}
        onMenuClick={setSelectedMenu}
        onSubMenuClick={setSelectedSubMenu}
        year={year}
        setYear={setYear}
        month={month}
        setMonth={setMonth}
        period={period}
        onPeriodChange={setPeriod}
      />
      <MainPanel year={year} month={month} period={period} selectedMenu={selectedMenu} selectedSubMenu={selectedSubMenu} />
      <ChatPanel />
    </div>
  );
}

export default App;
