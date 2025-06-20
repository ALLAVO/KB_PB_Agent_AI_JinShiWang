import React, { useState } from "react";
import "./App.css";
import kblogo from "./kblogo";

function Sidebar({ userName, menu, subMenu, onMenuClick, onSubMenuClick, selectedMenu, selectedSubMenu, period, onPeriodChange }) {
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
      <div className="sidebar-period">
        <select value={period} onChange={e => onPeriodChange(e.target.value)}>
          <option value="25.06.01 - 25.06.07">25.06.01 - 25.06.07</option>
          {/* 실제 구현시 기간 옵션 동적 생성 */}
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
