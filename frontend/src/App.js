import React, { useState } from "react";
import "./App.css";
import kblogo from "./kblogo";
import { getWeeksOfMonth } from "./weekUtils";

function Sidebar({ userName, menu, subMenu, onMenuClick, onSubMenuClick, selectedMenu, selectedSubMenu, period, onPeriodChange }) {
  // 연도/월 상태 추가
  const [year, setYear] = React.useState(2025);
  const [month, setMonth] = React.useState(6);

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
  // 실제 채팅 기능은 추후 구현
  return (
    <div className="chat-panel">
      <div className="chat-title">진시황과의 상담</div>
      <div className="chat-messages">
        {/* 채팅 메시지 영역 */}
      </div>
      <div className="chat-input-row">
        <input
          className="chat-input"
          placeholder="진시황에게 질문하세요...."
          value={input}
          onChange={e => setInput(e.target.value)}
        />
        <button className="chat-send-btn" disabled>
          <span role="img" aria-label="send">✈️</span>
        </button>
      </div>
    </div>
  );
}

function MainPanel() {
  return (
    <div className="main-panel">
      {/* 실제 데이터/그래프/뉴스 등은 추후 구현 */}
      <div className="main-placeholder">[2025년 6월 1주차] 시황 리포트 (데이터 영역)</div>
    </div>
  );
}

function App() {
  const [selectedMenu, setSelectedMenu] = useState("진시황의 혜안");
  const [selectedSubMenu, setSelectedSubMenu] = useState("시황");
  const [period, setPeriod] = useState("25.06.01 - 25.06.07");

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
        period={period}
        onPeriodChange={setPeriod}
      />
      <MainPanel />
      <ChatPanel />
    </div>
  );
}

export default App;
