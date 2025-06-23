import React, { useState } from "react";
import "./App.css";
import kblogo from "./kblogo";
import { getWeeksOfMonth } from "./weekUtils";
import sendIcon from "./assets/send.png";
import cloud1 from "./assets/cloud1.png";
import cloud2 from "./assets/cloud2.png";
import cloud3 from "./assets/cloud3.png";

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

function PipelinePanel({ name, year, month, weekStr }) {
  // 실제로는 API 연동 및 데이터 fetch 로직이 들어갈 예정
  return (
    <div className={`pipeline-panel pipeline-${name}`}>
      <div className="pipeline-title">{name.charAt(0).toUpperCase() + name.slice(1)} Pipeline</div>
      {/* TODO: {name} 데이터 API 연동 및 렌더링 */}
      <div className="pipeline-placeholder">[{year}년 {month}월 {weekStr}] {name} 데이터 영역</div>
    </div>
  );
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
