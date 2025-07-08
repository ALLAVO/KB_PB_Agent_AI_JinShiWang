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
            </>
          )}
        </>
      )}
    </div>
  );
}

function IndustryPipeline({ year, month, weekStr, period, onSetReportTitle, autoIndustryCategory, autoIndustryTrigger, onAutoIndustryDone }) {
  const [started, setStarted] = useState(false);
  const [inputSymbol, setInputSymbol] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [industryData, setIndustryData] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [showModal, setShowModal] = useState(false);
  
  // 산업 섹터 목록
  const sectors = [
    'Basic Materials',
    'Consumer Discretionary', 
    'Consumer Staples',
    'Energy',
    'Finance',
    'Health Care',
    'Industrials',
    'Miscellaneous',
    'Real Estate',
    'Technology',
    'Telecommunications',
    'Utilities'
  ];
  
  const chartData = '산업 차트 예시';
  const tableData = [
    { 산업: 'IT', 성장률: '5.2%' },
    { 산업: '바이오', 성장률: '3.1%' }
  ];
  const textSummary = `${year}년 ${month}월 ${weekStr} 산업 데이터 분석 요약입니다.`;

  // period에서 주차 시작일 추출
  const dateMatch = period.match(/(\d{2})\.(\d{2}) - (\d{2})\.(\d{2})/);
  let startDate = null;
  if (dateMatch) {
    const y = year;
    startDate = `${y}-${dateMatch[1]}-${dateMatch[2]}`;
  }

  const handleArticleClick = (article) => {
    setSelectedArticle(article);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedArticle(null);
  };

  // 자동 입력 및 자동 검색 트리거
  useEffect(() => {
    if (autoIndustryTrigger && autoIndustryCategory) {
      setInputSymbol(autoIndustryCategory);
      setTimeout(() => {
        handleSearch(autoIndustryCategory, true);
      }, 200);
    }
    // eslint-disable-next-line
  }, [autoIndustryTrigger, autoIndustryCategory]);

  const handleSearch = async (overrideCategory, isAuto) => {
    const categoryToUse = overrideCategory !== undefined ? overrideCategory : inputSymbol;
    if (!categoryToUse.trim()) {
      setError('산업군 이름을 입력해주세요');
      return;
    }
    
    setError("");
    setStarted(true);
    setLoading(true);
    setIndustryData(null);
    
    if (onSetReportTitle) {
      onSetReportTitle(`${categoryToUse.trim()} 산업 리포트`);
    }
    
    try {
      console.log('산업 API 호출', { sector: categoryToUse.trim(), startDate });
      const data = await fetchIndustryTop3Articles({ 
        sector: categoryToUse.trim(), 
        startDate: startDate 
      });
      setIndustryData(data);
      console.log('산업 데이터:', data);
    } catch (e) {
      console.error('산업 API 호출 오류:', e);
      setError('데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
      if (isAuto && onAutoIndustryDone) {
        onAutoIndustryDone();
      }
    }
  };

  // 섹터 버튼 클릭 핸들러
  const handleSectorClick = (sector) => {
    setInputSymbol(sector);
    if (error) setError("");
  };

  useEffect(() => {
    if (!started && onSetReportTitle) {
      onSetReportTitle('산업 리포트');
    }
    // eslint-disable-next-line
  }, [started]);

  return (
    <div>
      {!started && (
        <div className="industry-search-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          {/* 산업 섹터 버튼들 */}
          <div className="sector-selection-container">
            <h4 className="sector-selection-title">
              산업 섹터 선택
            </h4>
            <div className="sector-buttons-grid">
              {sectors.map((sector) => (
                <button
                  key={sector}
                  onClick={() => handleSectorClick(sector)}
                  className={`sector-button ${inputSymbol === sector ? 'selected' : ''}`}
                >
                  {sector}
                </button>
              ))}
            </div>
          </div>

          <label style={{marginBottom: 0}}>
            <input
              type="text"
              value={inputSymbol}
              onChange={e => { setInputSymbol(e.target.value); if (error) setError(""); }}
              className="industry-symbol-input center-text"
              placeholder="산업군 이름을 입력해주세요..."
            />
          </label>
          <button className="industry-search-btn" onClick={() => handleSearch()}>리포트 출력</button>
        </div>
      )}
      {started && (
        <>
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" />산업 Pipeline
          </div>
          <div className="pipeline-graph">
            <PipelineGraphSample />
          </div>
          
          {/* 전 주에 핫한 기사 Top 3 섹션 */}
          <div style={{ marginTop: '24px', marginBottom: '24px' }}>
            <h3 style={{ 
              fontSize: '20px', 
              fontWeight: 'bold', 
              marginBottom: '16px',
              color: '#333',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>🔥</span>
              전 주에 핫한 기사 Top 3
            </h3>
            
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                AI가 산업 트렌드를 분석하고 있습니다...
              </div>
            ) : error && error !== '산업군 이름을 입력해주세요' ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#d32f2f' }}>
                {error}
              </div>
            ) : industryData && industryData.top3_articles && industryData.top3_articles.length > 0 ? (
              <ol style={{ marginTop: '8px' }}>
                {industryData.top3_articles.map((art, idx) => (
                  <li key={idx} style={{ marginBottom: '20px', padding: '16px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #e9ecef' }}>
                    {/* 기사 제목 */}
                    <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '12px' }}>
                      {art.article_title}
                      <span style={{ marginLeft: '10px', color: '#0077cc', fontWeight: 'normal', fontSize: '14px' }}>
                        [{art.stock_symbol}]
                      </span>
                    </div>
                    
                    {/* 감성점수 (한 줄 띄고 표시) */}
                    <div style={{ fontSize: '15px', color: '#0077cc', marginBottom: '8px' }}>
                      감성점수: {art.score > 0 ? '+' : ''}{art.score}
                    </div>
                    
                    {/* 기사 작성 날짜 */}
                    <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>{art.date}</div>
                    
                    {/* 기사 키워드 */}
                    {art.keywords && art.keywords.length > 0 && (
                      <div style={{
                        margin: '8px 0',
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '4px'
                      }}>
                        {art.keywords.slice(0, 5).map((keyword, idx) => (
                          <span
                            key={idx}
                            style={{
                              backgroundColor: '#e3f2fd',
                              color: '#1976d2',
                              fontSize: '11px',
                              padding: '2px 6px',
                              borderRadius: '12px',
                              border: '1px solid #bbdefb',
                              display: 'inline-block',
                              fontWeight: '500'
                            }}
                          >
                            #{keyword}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    {/* 기사 요약 */}
                    {art.summary && (
                      <div style={{
                        fontSize: '13px',
                        color: '#555',
                        backgroundColor: '#ffffff',
                        padding: '12px',
                        borderRadius: '6px',
                        border: '1px solid #e0e0e0',
                        margin: '8px 0',
                        lineHeight: '1.5'
                      }}>
                        <div style={{ fontWeight: 'bold', fontSize: '12px', color: '#6c757d', marginBottom: '6px' }}>
                          📄 기사 요약
                        </div>
                        {art.summary}
                      </div>
                    )}
                    
                    {/* 기사 본문 확인 버튼 */}
                    <button 
                      onClick={() => handleArticleClick(art)}
                      style={{
                        backgroundColor: '#0077cc',
                        color: 'white',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer',
                        marginTop: '8px'
                      }}
                    >
                      기사 본문 자세히 확인하기
                    </button>
                  </li>
                ))}
              </ol>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                해당 산업의 데이터가 없습니다.
              </div>
            )}
          </div>
          
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
          {/* <div className="pipeline-text">{textSummary}</div> */}
          
          {/* 기사 상세 모달 */}
          {showModal && selectedArticle && (
            <div style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              zIndex: 1000
            }}>
              <div style={{
                backgroundColor: 'white',
                padding: '24px',
                borderRadius: '8px',
                maxWidth: '80%',
                maxHeight: '80%',
                overflow: 'auto',
                position: 'relative',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
              }}>
                <button 
                  onClick={closeModal}
                  style={{
                    position: 'absolute',
                    top: '12px',
                    right: '12px',
                    backgroundColor: 'transparent',
                    border: 'none',
                    fontSize: '20px',
                    cursor: 'pointer',
                    color: '#666'
                  }}
                >
                  ×
                </button>
                
                <div style={{ marginRight: '30px' }}>
                  <h2 style={{
                    fontSize: '20px',
                    fontWeight: 'bold',
                    marginBottom: '12px',
                    color: '#333',
                    lineHeight: '1.4'
                  }}>
                    {selectedArticle.article_title}
                  </h2>
                  
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '16px',
                    gap: '16px'
                  }}>
                    <span style={{
                      fontSize: '14px',
                      color: '#666',
                      backgroundColor: '#f5f5f5',
                      padding: '4px 8px',
                      borderRadius: '4px'
                    }}>
                      {selectedArticle.date}
                    </span>
                    <span style={{
                      fontSize: '14px',
                      color: '#666',
                      backgroundColor: '#e3f2fd',
                      padding: '4px 8px',
                      borderRadius: '4px'
                    }}>
                      {selectedArticle.stock_symbol}
                    </span>
                    <span style={{
                      fontSize: '16px',
                      fontWeight: 'bold',
                      color: selectedArticle.score > 0 ? '#22c55e' : selectedArticle.score < 0 ? '#ef4444' : '#666',
                      backgroundColor: '#f9f9f9',
                      padding: '4px 8px',
                      borderRadius: '4px'
                    }}>
                      감성점수: {selectedArticle.score > 0 ? '+' : ''}{selectedArticle.score}
                    </span>
                  </div>
                  
                  <div style={{
                    fontSize: '15px',
                    lineHeight: '1.6',
                    color: '#444',
                    textAlign: 'justify',
                    maxHeight: '400px',
                    overflowY: 'auto',
                    padding: '16px',
                    backgroundColor: '#fafafa',
                    borderRadius: '6px',
                    border: '1px solid #e0e0e0'
                  }}>
                    {selectedArticle.article}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MainPanel({ year, month, period, selectedMenu, selectedSubMenu, autoCustomerName, autoCustomerTrigger, onAutoCustomerDone, setSelectedMenu, autoCompanySymbol, autoCompanyTrigger, onAutoCompanyDone, setSelectedSubMenu, autoIndustryCategory, autoIndustryTrigger, onAutoIndustryDone, autoMarketTrigger }) {
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
          />
        )}
      </div>
    </div>
  );
}

function PipelinePanel({ name, year, month, weekStr, period, onSetReportTitle, autoCustomerName, autoCustomerTrigger, onAutoCustomerDone, autoCompanySymbol, autoCompanyTrigger, onAutoCompanyDone, autoIndustryCategory, autoIndustryTrigger, onAutoIndustryDone, autoStartMarket }) {
  if (name === 'customer') return <ClientPipeline year={year} month={month} weekStr={weekStr} period={period} onSetReportTitle={onSetReportTitle} autoCustomerName={autoCustomerName} autoCustomerTrigger={autoCustomerTrigger} onAutoCustomerDone={onAutoCustomerDone} />;
  if (name === 'market') return <MarketPipeline year={year} month={month} weekStr={weekStr} period={period} autoStart={autoStartMarket} />;
  if (name === 'industry') return <IndustryPipeline year={year} month={month} weekStr={weekStr} period={period} onSetReportTitle={onSetReportTitle} autoIndustryCategory={autoIndustryCategory} autoIndustryTrigger={autoIndustryTrigger} onAutoIndustryDone={onAutoIndustryDone} />;
  if (name === 'company') return <CompanyPipeline year={year} month={month} weekStr={weekStr} period={period} onSetReportTitle={onSetReportTitle} autoCompanySymbol={autoCompanySymbol} autoCompanyTrigger={autoCompanyTrigger} onAutoCompanyDone={onAutoCompanyDone} />;
  return null;
}

function App() {
  const [selectedMenu, setSelectedMenu] = useState("진시황의 혜안");
  const [selectedSubMenu, setSelectedSubMenu] = useState("증시");
  const [year, setYear] = useState(2025);
  const [month, setMonth] = useState(6);
  const [period, setPeriod] = useState("06.01 - 06.07 (1주차)");
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

function PipelineGraphSample() {
  // 6개월치 Apple 주가 임의 데이터 (월별 종가)
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
  const pointRadius = 4;
  const xStep = (width - 2 * padding - yAxisWidth) / (data.length - 1);
  const yScale = price => padding + ((maxValue - price) / (maxValue - minValue || 1)) * (height - 2 * padding);

  // 평균선 y좌표
  const avgY = yScale(avgValue);

  // 구간별로 평균보다 높은 구간(빨간색), 낮은 구간(파란색)으로 선분 분리
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
      // 평균선과의 교점 계산
      const t = (avgValue - data[i].price) / (data[i + 1].price - data[i].price);
      const crossX = x1 + t * (x2 - x1);
      const crossY = avgY;
      segments.push({ x1, y1, x2: crossX, y2: crossY, color: above1 ? '#ef4444' : '#3b82f6' });
      segments.push({ x1: crossX, y1: crossY, x2, y2, color: above2 ? '#ef4444' : '#3b82f6' });
    }
  }

  // Y축 눈금 (5 단위)
  const yTicks = [];
  const tickStep = 5;
  for (let v = Math.ceil(minValue / tickStep) * tickStep; v <= maxValue; v += tickStep) {
    yTicks.push(v);
  }

  return (
    <div className="pipeline-graph-sample">
      <svg width={width} height={height} className="line-graph-svg">
        {/* Y축 */}
        <line x1={padding + yAxisWidth} y1={padding} x2={padding + yAxisWidth} y2={height - padding} stroke="#bbb" strokeWidth="1" />
        {/* X축 */}
        <line x1={padding + yAxisWidth} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#bbb" strokeWidth="1" />
        {/* Y축 눈금 및 라벨, 얇은 실선 */}
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
        {/* 평균선 */}
        <line x1={padding + yAxisWidth} y1={avgY} x2={width - padding} y2={avgY} stroke="#888" strokeDasharray="4 2" strokeWidth="1.5" />
        <text x={width - padding + 4} y={avgY + 4} fontSize="12" fill="#888">평균 {avgValue.toFixed(1)}</text>
        {/* 데이터 라인 (구간별 색상) */}
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
        {/* 월 라벨 */}
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

export default App;