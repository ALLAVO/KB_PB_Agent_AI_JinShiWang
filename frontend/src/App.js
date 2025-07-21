import React, { useState, useEffect } from "react";
import "./App.css";
import "./components/industry_pipeline/IndustryPipeline.css";
import kblogo from "./kblogo";
import { getWeeksOfMonth } from "./weekUtils";
import sendIcon from "./assets/send.png";
import cloud1 from "./assets/cloud1.png";
import cloud2 from "./assets/cloud2.png";
import cloud3 from "./assets/cloud3.png";
import titlecloud from "./assets/titlecloud.png";
import {fetchIndustryTop3Articles } from "./api/industry";
import {fetchIndices6MonthsChart, fetchTreasuryYields6MonthsChart, fetchFx6MonthsChart, fetchIndices1YearChart, fetchTreasuryYields1YearChart, fetchFx1YearChart} from "./api/market";
import {fetchIntention} from "./api/intention";
import StockChart from "./components/company_pipeline/StockChart";
import MarketIndicesChart from "./components/market_pipeline/MarketIndicesChart";
import CombinedFinancialChart from "./components/market_pipeline/FICCchart";
import IntroScreen from "./components/etc/IntroScreen";
import IntentionForm from "./components/etc/IntentionForm";
import MarketIndices1YearTable from "./components/market_pipeline/MarketIndices1YearTable";
import FiccTable1Year from "./components/market_pipeline/FiccTable1Year";
import CompanyPipeline from "./components/company_pipeline/CompanyPipeline";
import ClientPipeline from "./components/client_pipeline/ClientPipeline";
import IndustryPipeline from "./components/industry_pipeline/IndustryPipeline";
import HotArticles from "./components/market_pipeline/HotArticles";

function CloudDecorations() {
  return (
    <>
      <img src={cloud1} alt="cloud1" className="cloud-decoration cloud1" />
      <img src={cloud2} alt="cloud2" className="cloud-decoration cloud2" />
      <img src={cloud3} alt="cloud3" className="cloud-decoration cloud3" />
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

function ChatPanel({ onPersonalIntent, onEnterpriseIntent, onIndustryIntent, onMarketIntent }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  // textarea 높이 자동 조절
  const textareaRef = React.useRef(null);
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [input]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = { role: "user", content: input };
    setMessages(msgs => [...msgs, userMsg]);
    setLoading(true);
    try {
      const result = await fetchIntention(input);
      let botMsg = "";
      if (result && result.intent) {
        if (result.intent === "market") {
          botMsg = "진시황이 증시정보에 대해 조사 중입니다...";
          if (onMarketIntent) onMarketIntent();
        } else if (result.intent === "industry") {
          botMsg = `진시황이 ${result.industry_keyword || ''} 산업에 대해 조사 중입니다...`;
          if (result.category && onIndustryIntent) {
            onIndustryIntent(result.category);
          }
        } else if (result.intent === "enterprise") {
          botMsg = `진시황이 ${result.company_name || ''}에 대해서 조사 중입니다...`;
          if (result.symbol && onEnterpriseIntent) {
            onEnterpriseIntent(result.symbol);
          }
        } else if (result.intent === "personal") {
          botMsg = `진시황이 ${result.customer_name || ''} 고객님에 대해 조사 중입니다...`;
          if (result.customer_name && onPersonalIntent) {
            onPersonalIntent(result.customer_name);
          }
        } else if (result.intent === "fallback" && result.answer) {
          botMsg = result.answer;
        } else {
          botMsg = JSON.stringify(result, null, 2);
        }
      } else {
        botMsg = JSON.stringify(result, null, 2);
      }
      setMessages(msgs => [...msgs, { role: "bot", content: botMsg }]);
    } catch (e) {
      setMessages(msgs => [...msgs, { role: "bot", content: "오류가 발생했습니다." }]);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel chat-panel-relative">
      <div className="chat-title-row">
        <div className="chat-title">진시황과의 상담</div>
        <div className="chat-title-buttons">
          <button className="chat-title-btn">
            <img src={require("./assets/plus.png")} alt="plus" style={{ width: 24, height: 24 }} />
          </button>
          <button className="chat-title-btn">
            <img src={require("./assets/stack.png")} alt="stack" style={{ width: 24, height: 24 }} />
          </button>
        </div>
      </div>
      <div className="chat-messages">
        <CloudDecorations />
        {/* 채팅 메시지 영역 */}
        <div className="chat-message-list">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message chat-message-${msg.role}`}>
              {/* {msg.role === "user" ? "🙋‍♂️ " : "🤖 "} */}
              <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
            </div>
          ))}
          {loading && (
            <div className="chat-message chat-message-bot"> <span>답변 생성 중...</span></div>
          )}
        </div>
      </div>
      <div className="chat-input-row">
        <div className="chat-input-bg">
          <textarea
            ref={textareaRef}
            className="chat-input"
            placeholder="진시황에게 질문하세요..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={loading}
          />
        </div>
        <button className="chat-send-btn" onClick={handleSend} disabled={!input.trim() || loading}>
          <img src={sendIcon} alt="send" className="chat-send-icon" />
        </button>
      </div>
    </div>
  );
}

function CustomerPipeline({ year, month, weekStr, onSetReportTitle, autoCustomerName, autoCustomerTrigger, onAutoCustomerDone }) {
  const [started, setStarted] = useState(false);
  const [inputSymbol, setInputSymbol] = useState("");
  const [error, setError] = useState("");
  const chartData = '고객 차트 예시';
  const tableData = [
    { 이름: '홍길동', 등급: 'Gold', 최근방문: '2025-06-01' },
    { 이름: '김철수', 등급: 'Silver', 최근방문: '2025-06-03' }
  ];
  const textSummary = `${year}년 ${month}월 ${weekStr} 고객 데이터 분석 요약입니다.`;

  // 자동 입력 및 자동 검색 트리거
  useEffect(() => {
    if (autoCustomerTrigger && autoCustomerName) {
      setInputSymbol(autoCustomerName);
      setTimeout(() => {
        handleSearch(autoCustomerName, true);
      }, 200); // 약간의 딜레이로 렌더링 보장
    }
    // eslint-disable-next-line
  }, [autoCustomerTrigger, autoCustomerName]);

  const handleSearch = (overrideName, isAuto) => {
    const nameToUse = overrideName !== undefined ? overrideName : inputSymbol;
    if (!nameToUse.trim()) {
      setError('고객님 성함을 입력해주세요');
      return;
    }
    setError("");
    setStarted(true);
    if (onSetReportTitle) {
      onSetReportTitle(`${nameToUse.trim()}님 리포트`);
    }
    if (isAuto && onAutoCustomerDone) {
      onAutoCustomerDone();
    }
  };

  useEffect(() => {
    if (!started && onSetReportTitle) {
      onSetReportTitle('고객 리포트');
    }
    // eslint-disable-next-line
  }, [started]);

  return (
    <div>
      {!started && (
        <div className="customer-search-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          <label style={{marginBottom: 0}}>
            <input
              type="text"
              value={inputSymbol}
              onChange={e => { setInputSymbol(e.target.value); if (error) setError(""); }}
              className="customer-symbol-input center-text"
              placeholder="고객님 성함을 입력해주세요..."
            />
          </label>
          <button className="customer-search-btn" onClick={() => handleSearch()}>리포트 출력</button>
        </div>
      )}
      {started && (
        <>
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
        </>
      )}
    </div>
  );
}

function MarketPipeline({ year, month, weekStr, period, autoStart }) {
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [indicesData, setIndicesData] = useState(null);
  const [treasuryData, setTreasuryData] = useState(null);
  const [fxData, setFxData] = useState(null);
  const [indices1YearData, setIndices1YearData] = useState(null);
  const [treasuryData1Year, setTreasuryData1Year] = useState(null);
  const [fxData1Year, setFxData1Year] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (autoStart) {
      handleStartReport();
    }
  }, [autoStart, year, month, period]);

  // 연/월/주차가 변경될 때 기존 데이터 초기화
  useEffect(() => {
    if (started && !autoStart) {
      // 자동 시작이 아닌 경우에만 데이터 초기화
      setIndicesData(null);
      setTreasuryData(null);
      setFxData(null);
      setIndices1YearData(null);
      setTreasuryData1Year(null);
      setFxData1Year(null);
      setError("");
    }
  }, [year, month, period]);

  const handleStartReport = async () => {
    setStarted(true);
    setLoading(true);
    setError("");
    setIndicesData(null);
    setTreasuryData(null);
    setFxData(null);
    setIndices1YearData(null);
    setTreasuryData1Year(null);
    setFxData1Year(null);

    // period에서 종료일 추출하여 endDate로 사용
    const dateMatch = period.match(/(\d{2})\.(\d{2}) - (\d{2})\.(\d{2})/);
    let endDate;
    if (dateMatch) {
      // 주차의 종료일을 endDate로 사용
      endDate = `${year}-${dateMatch[3]}-${dateMatch[4]}`;
    } else {
      // period 파싱에 실패하면 현재 날짜 사용
      endDate = new Date().toISOString().split('T')[0];
    }

    try {
      // 6개 API를 병렬로 호출 (1년치 FICC 데이터 추가)
      const [indices, treasury, fx, indices1Year, treasury1Year, fx1Year] = await Promise.all([
        fetchIndices6MonthsChart(endDate),
        fetchTreasuryYields6MonthsChart(endDate),
        fetchFx6MonthsChart(endDate),
        fetchIndices1YearChart(endDate),
        fetchTreasuryYields1YearChart(endDate),
        fetchFx1YearChart(endDate)
      ]);

      setIndicesData(indices);
      setTreasuryData(treasury);
      setFxData(fx);
      setIndices1YearData(indices1Year);
      setTreasuryData1Year(treasury1Year);
      setFxData1Year(fx1Year);
      
      console.log('Market data loaded:', { indices, treasury, fx, indices1Year, treasury1Year, fx1Year });
    } catch (e) {
      console.error('Market API 호출 오류:', e);
      setError('시장 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const chartData = '시장 차트 예시';
  
  return (
    <div>
      {!started && (
        <button
          className="report-start-btn"
          onClick={handleStartReport}
        >
          리포트 출력
        </button>
      )}
      {started && (
        <>
          {/* 로딩 또는 에러 표시 */}
          {loading && (
            <div className="market-loading-message">
              시장 데이터를 불러오는 중...
            </div>
          )}

          {error && (
            <div className="market-error-message">
              {error}
            </div>
          )}

          {/* 차트들 */}
          {!loading && !error && (
            <>
              <div className="pipeline-title">
                <img src={titlecloud} alt="cloud" /> 미국 증시 동향
              </div>
              <MarketIndicesChart 
                data={indicesData} 
                loading={loading} 
                error={indicesData?.error} 
              />
              <MarketIndices1YearTable indices1YearData={indices1YearData} loading={loading} error={error} />
              {/* 핫한 기사 섹션을 CombinedFinancialChart 위로 이동 */}
              <HotArticles 
                year={year}
                month={month}
                weekStr={weekStr}
                period={period}
                autoStart={true}
              />
              <div className="pipeline-title">
                <img src={titlecloud} alt="cloud" /> FICC
              </div>
              <CombinedFinancialChart 
                treasuryData={treasuryData} 
                fxData={fxData}
                loading={loading} 
                error={treasuryData?.error || fxData?.error} 
              />
              <FiccTable1Year 
                treasuryData1Year={treasuryData1Year}
                fxData1Year={fxData1Year}
                loading={loading}
                error={treasuryData1Year?.error || fxData1Year?.error}
              />
              <div style={{height: '50px'}}></div>
            </>
          )}
        </>
      )}
    </div>
  );
}

function MainPanel({ year, month, period, selectedMenu, selectedSubMenu, autoCustomerName, autoCustomerTrigger, onAutoCustomerDone, setSelectedMenu, autoCompanySymbol, autoCompanyTrigger, onAutoCompanyDone, setSelectedSubMenu, autoIndustryCategory, autoIndustryTrigger, onAutoIndustryDone, autoMarketTrigger, onStockClick, onIndustryClick, onMarketClick }) {
  // 주차 정보 추출 (예: "(1주차)")
  const weekMatch = period.match(/\((\d+주차)\)/);
  const weekStr = weekMatch ? weekMatch[1] : "";

  // 주차 시작일, 종료일 추출 (예: "06.01 - 06.07 (1주차)")
  const dateMatch = period.match(/(\d{2})\.(\d{2}) - (\d{2})\.(\d{2})/);
  let startDate = null;
  let endDate = null;
  if (dateMatch) {
    const y = year;
    startDate = `${y}-${dateMatch[1]}-${dateMatch[2]}`;
    endDate = `${y}-${dateMatch[3]}-${dateMatch[4]}`;
  }

  // 메뉴/서브메뉴에 따라 보여줄 pipeline 결정
  let pipelineName = null;
  let defaultReportTitle = '';
  let autoStartMarket = false;
  if (selectedMenu === "고객 관리") {
    pipelineName = "customer";
    defaultReportTitle = "고객 리포트";
  } else if (selectedMenu === "진시황의 혜안") {
    if (selectedSubMenu === "증시") {
      pipelineName = "market";
      defaultReportTitle = "증시 리포트";
      if (autoMarketTrigger) autoStartMarket = true;
    } else if (selectedSubMenu === "산업") {
      pipelineName = "industry";
      defaultReportTitle = "산업 리포트";
    } else if (selectedSubMenu === "기업") {
      pipelineName = "company";
      defaultReportTitle = "기업 리포트";
    }
  }

  const [reportTitle, setReportTitle] = useState(defaultReportTitle);
  useEffect(() => {
    setReportTitle(defaultReportTitle);
    // eslint-disable-next-line
  }, [selectedMenu, selectedSubMenu, year, month, period]);

  // 자동 고객 리포트 트리거 감지
  useEffect(() => {
    if (autoCustomerTrigger && autoCustomerName && selectedMenu !== "고객 관리") {
      setSelectedMenu("고객 관리");
    }
  }, [autoCustomerTrigger, autoCustomerName, selectedMenu, setSelectedMenu]);
  useEffect(() => {
    if (autoCompanyTrigger && autoCompanySymbol && (selectedMenu !== "진시황의 혜안" || selectedSubMenu !== "기업")) {
      setSelectedMenu("진시황의 혜안");
      setSelectedSubMenu("기업");
    }
  }, [autoCompanyTrigger, autoCompanySymbol, selectedMenu, selectedSubMenu, setSelectedMenu, setSelectedSubMenu]);
  useEffect(() => {
    if (autoIndustryTrigger && autoIndustryCategory && (selectedMenu !== "진시황의 혜안" || selectedSubMenu !== "산업")) {
      setSelectedMenu("진시황의 혜안");
      setSelectedSubMenu("산업");
    }
  }, [autoIndustryTrigger, autoIndustryCategory, selectedMenu, selectedSubMenu, setSelectedMenu, setSelectedSubMenu]);

  return (
    <div className="main-panel">
      <div className="main-title">[{year}년 {month}월 {(() => {const weekMatch = period.match(/\((\d+주차)\)/); return weekMatch ? weekMatch[1] : "";})()}] {reportTitle}</div>
      <div className="main-placeholder" style={{marginTop: '32px'}}>
        {pipelineName && (
          <PipelinePanel
            name={pipelineName}
            year={year}
            month={month}
            weekStr={(() => {const weekMatch = period.match(/\((\d+주차)\)/); return weekMatch ? weekMatch[1] : "";})()}
            period={period}
            onSetReportTitle={['industry','company','customer'].includes(pipelineName) ? setReportTitle : undefined}
            autoCustomerName={pipelineName === 'customer' ? autoCustomerName : undefined}
            autoCustomerTrigger={pipelineName === 'customer' ? autoCustomerTrigger : undefined}
            onAutoCustomerDone={pipelineName === 'customer' ? onAutoCustomerDone : undefined}
            autoCompanySymbol={pipelineName === 'company' ? autoCompanySymbol : undefined}
            autoCompanyTrigger={pipelineName === 'company' ? autoCompanyTrigger : undefined}
            onAutoCompanyDone={pipelineName === 'company' ? onAutoCompanyDone : undefined}
            autoIndustryCategory={pipelineName === 'industry' ? autoIndustryCategory : undefined}
            autoIndustryTrigger={pipelineName === 'industry' ? autoIndustryTrigger : undefined}
            onAutoIndustryDone={pipelineName === 'industry' ? onAutoIndustryDone : undefined}
            autoStartMarket={pipelineName === 'market' ? autoStartMarket : undefined}
            onStockClick={onStockClick}
            onIndustryClick={onIndustryClick}
            onMarketClick={onMarketClick}
          />
        )}
      </div>
    </div>
  );
}

function PipelinePanel({ name, year, month, weekStr, period, onSetReportTitle, autoCustomerName, autoCustomerTrigger, onAutoCustomerDone, autoCompanySymbol, autoCompanyTrigger, onAutoCompanyDone, autoIndustryCategory, autoIndustryTrigger, onAutoIndustryDone, autoStartMarket, onStockClick, onIndustryClick, onMarketClick }) {
  if (name === 'customer') return <ClientPipeline year={year} month={month} weekStr={weekStr} period={period} onSetReportTitle={onSetReportTitle} autoCustomerName={autoCustomerName} autoCustomerTrigger={autoCustomerTrigger} onAutoCustomerDone={onAutoCustomerDone} onStockClick={onStockClick} onIndustryClick={onIndustryClick} onMarketClick={onMarketClick} />;
  if (name === 'market') return <MarketPipeline year={year} month={month} weekStr={weekStr} period={period} autoStart={autoStartMarket} />;
  if (name === 'industry') return <IndustryPipeline year={year} month={month} weekStr={weekStr} period={period} onSetReportTitle={onSetReportTitle} autoIndustryCategory={autoIndustryCategory} autoIndustryTrigger={autoIndustryTrigger} onAutoIndustryDone={onAutoIndustryDone} onStockClick={onStockClick} />;
  if (name === 'company') return <CompanyPipeline year={year} month={month} weekStr={weekStr} period={period} onSetReportTitle={onSetReportTitle} autoCompanySymbol={autoCompanySymbol} autoCompanyTrigger={autoCompanyTrigger} onAutoCompanyDone={onAutoCompanyDone} onIndustryClick={onIndustryClick} onMarketClick={onMarketClick} />;
  return null;
}

function App() {
  const [selectedMenu, setSelectedMenu] = useState("고객 관리");
  const [selectedSubMenu, setSelectedSubMenu] = useState(""); // 고객 관리에는 서브메뉴 없음
  const [year, setYear] = useState(2023);
  const [month, setMonth] = useState(5);
  const [period, setPeriod] = useState("05.14 - 05.20 (3주차)");
  const [showIntro, setShowIntro] = useState(true);
  // 자동 고객/기업/산업 리포트 트리거 상태 추가
  const [autoCustomerName, setAutoCustomerName] = useState("");
  const [autoCustomerTrigger, setAutoCustomerTrigger] = useState(false);
  const [autoCompanySymbol, setAutoCompanySymbol] = useState("");
  const [autoCompanyTrigger, setAutoCompanyTrigger] = useState(false);
  const [autoIndustryCategory, setAutoIndustryCategory] = useState("");
  const [autoIndustryTrigger, setAutoIndustryTrigger] = useState(false);
  const [autoMarketTrigger, setAutoMarketTrigger] = useState(false);

  const handleStart = () => {
    setShowIntro(false);
  };

  // 자동 트리거 후 상태 초기화
  const handleAutoCustomerDone = () => {
    setAutoCustomerName("");
    setAutoCustomerTrigger(false);
  };
  const handleAutoCompanyDone = () => {
    setAutoCompanySymbol("");
    setAutoCompanyTrigger(false);
  };
  const handleAutoIndustryDone = () => {
    setAutoIndustryCategory("");
    setAutoIndustryTrigger(false);
  };

  // 종목 클릭 핸들러 (기업 파이프라인으로 이동)
  const handleStockClick = (stockSymbol) => {
    setSelectedMenu("진시황의 혜안");
    setSelectedSubMenu("기업");
    setAutoCompanySymbol(stockSymbol);
    setAutoCompanyTrigger(true);
  };

  // 산업 클릭 핸들러 (산업 파이프라인으로 이동)
  const handleIndustryClick = (industryCategory) => {
    setSelectedMenu("진시황의 혜안");
    setSelectedSubMenu("산업");
    setAutoIndustryCategory(industryCategory);
    setAutoIndustryTrigger(true);
  };

  // 증시 클릭 핸들러 (증시 파이프라인으로 이동)
  const handleMarketClick = () => {
    setSelectedMenu("진시황의 혜안");
    setSelectedSubMenu("증시");
    setAutoMarketTrigger(true);
  };

  if (showIntro) {
    return <IntroScreen onStart={handleStart} />;
  }

  return (
    <div className="app-layout">
      <Sidebar
        userName="김PB"
        menu={["진시황의 혜안", "고객 관리"]}
        subMenu={["증시", "산업", "기업"]}
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
      <MainPanel
        year={year}
        month={month}
        period={period}
        selectedMenu={selectedMenu}
        selectedSubMenu={selectedSubMenu}
        autoCustomerName={autoCustomerName}
        autoCustomerTrigger={autoCustomerTrigger}
        onAutoCustomerDone={handleAutoCustomerDone}
        setSelectedMenu={setSelectedMenu}
        autoCompanySymbol={autoCompanySymbol}
        autoCompanyTrigger={autoCompanyTrigger}
        onAutoCompanyDone={handleAutoCompanyDone}
        setSelectedSubMenu={setSelectedSubMenu}
        autoIndustryCategory={autoIndustryCategory}
        autoIndustryTrigger={autoIndustryTrigger}
        onAutoIndustryDone={handleAutoIndustryDone}
        autoMarketTrigger={autoMarketTrigger}
        onStockClick={handleStockClick}
        onIndustryClick={handleIndustryClick}
        onMarketClick={handleMarketClick}
      />
      <ChatPanel
        onPersonalIntent={(customerName) => {
          setSelectedMenu("고객 관리");
          setAutoCustomerName(customerName);
          setAutoCustomerTrigger(true);
        }}
        onEnterpriseIntent={(symbol) => {
          setSelectedMenu("진시황의 혜안");
          setSelectedSubMenu("기업");
          setAutoCompanySymbol(symbol);
          setAutoCompanyTrigger(true);
        }}
        onIndustryIntent={(category) => {
          setSelectedMenu("진시황의 혜안");
          setSelectedSubMenu("산업");
          setAutoIndustryCategory(category);
          setAutoIndustryTrigger(true);
        }}
        onMarketIntent={() => {
          setSelectedMenu("진시황의 혜안");
          setSelectedSubMenu("증시");
          setAutoMarketTrigger(true);
          setTimeout(() => setAutoMarketTrigger(false), 1000);
        }}
      />
    </div>
  );
}

export default App;