import logo from './logo.svg';
import './App.css';
import React, { useState } from "react";
import { getWeeksOfMonth } from "./weekUtils";

function App() {
  const [customerName, setCustomerName] = useState("");
  const [pbName, setPbName] = useState("");
  const [investmentPropensity, setInvestmentPropensity] = useState("");
  const [createdCustomer, setCreatedCustomer] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [companySymbol, setCompanySymbol] = useState("");
  const [companyInfo, setCompanyInfo] = useState(null);
  // 포트폴리오 입력 관련 상태
  const [portfolioList, setPortfolioList] = useState([]);
  const [stockSymbolInput, setStockSymbolInput] = useState("");
  const [quantityInput, setQuantityInput] = useState("");
  const [priceInput, setPriceInput] = useState("");
  const [predictionResult, setPredictionResult] = useState(null);
  const [reportResult, setReportResult] = useState(null);
  // 날짜 입력 상태를 App 전체에서 공통으로 사용
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1); // 1~12
  const weeks = getWeeksOfMonth(year, month);
  const today = new Date();
  // 오늘 이후가 포함된 주차는 제외
  const validWeeks = weeks.filter(w => w.start <= today && w.end <= today || (w.start <= today && w.end >= today));
  const [selectedWeekIdx, setSelectedWeekIdx] = useState(0);
  const [startDate, setStartDate] = useState(validWeeks.length > 0 ? validWeeks[0].start.toISOString().slice(0, 10) : "");
  const [endDate, setEndDate] = useState(validWeeks.length > 0 ? validWeeks[0].end.toISOString().slice(0, 10) : "");

  // 주차 선택 시 startDate, endDate 자동 반영
  React.useEffect(() => {
    if (validWeeks.length > 0 && selectedWeekIdx < validWeeks.length) {
      setStartDate(validWeeks[selectedWeekIdx].start.toISOString().slice(0, 10));
      setEndDate(validWeeks[selectedWeekIdx].end.toISOString().slice(0, 10));
    }
  }, [selectedWeekIdx, year, month]);

  // 감성점수 조회 관련 상태
  const [sentimentSymbol, setSentimentSymbol] = useState("");
  const [sentimentYear, setSentimentYear] = useState(new Date().getFullYear());
  const [sentimentMonth, setSentimentMonth] = useState(new Date().getMonth() + 1); // 1~12
  const [sentimentWeek, setSentimentWeek] = useState(1);
  const [sentimentResult, setSentimentResult] = useState(null);
  const [sentimentLoading, setSentimentLoading] = useState(false);
  const [sentimentError, setSentimentError] = useState("");

  // 포트폴리오 항목 추가
  const addPortfolioItem = () => {
    if (!stockSymbolInput || !quantityInput || !priceInput) return;
    setPortfolioList([
      ...portfolioList,
      {
        stock_symbol: stockSymbolInput,
        quantity: Number(quantityInput),
        average_purchase_price: Number(priceInput),
      },
    ]);
    setStockSymbolInput("");
    setQuantityInput("");
    setPriceInput("");
  };

  // 포트폴리오 항목 삭제
  const removePortfolioItem = (idx) => {
    setPortfolioList(portfolioList.filter((_, i) => i !== idx));
  };

  // 고객 생성
  const createCustomer = async () => {
    const res = await fetch("http://localhost:8000/api/v1/customers/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: customerName,
        pb_name: pbName,
        investment_propensity: investmentPropensity,
        investment_portfolio: portfolioList,
      }),
    });
    setCreatedCustomer(await res.json());
  };

  // 고객 목록 조회
  const fetchCustomers = async () => {
    const res = await fetch("http://localhost:8000/api/v1/customers/");
    setCustomers(await res.json());
  };

  // 기업 정보 조회
  const fetchCompany = async () => {
    let url = `http://localhost:8000/api/v1/companies/${companySymbol}`;
    const params = [];
    if (startDate) params.push(`start_date=${startDate}`);
    if (endDate) params.push(`end_date=${endDate}`);
    if (params.length > 0) url += `?${params.join("&")}`;
    const res = await fetch(url);
    const data = await res.json();
    // 196줄까지(재무제표 포함) 보여주기 위해 그대로 저장
    setCompanyInfo(data);
  };

  // 예측 요청
  const createPrediction = async () => {
    if (!createdCustomer) return alert("먼저 고객을 생성하세요");
    if (portfolioList.length === 0) return alert("포트폴리오를 1개 이상 입력하세요");
    const stock_symbol = portfolioList[0].stock_symbol;
    const res = await fetch("http://localhost:8000/api/v1/predictions/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: createdCustomer.id,
        stock_symbol,
      }),
    });
    setPredictionResult(await res.json());
  };

  // 보고서 생성
  const createReport = async () => {
    if (!createdCustomer || !predictionResult) return alert("고객과 예측을 먼저 생성하세요");
    const res = await fetch("http://localhost:8000/api/v1/reports/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: createdCustomer.id,
        stock_symbol: predictionResult.stock_symbol,
        highlight_news: ["테스트 뉴스1", "테스트 뉴스2"]
      }),
    });
    setReportResult(await res.json());
  };

  // 감성점수 조회 함수 수정
  const fetchSentimentScores = async () => {
    if (!sentimentSymbol || !startDate || !endDate) {
      setSentimentError("기업명, 시작일, 종료일을 모두 입력하세요.");
      return;
    }
    setSentimentLoading(true);
    setSentimentError("");
    setSentimentResult(null);
    try {
      const params = new URLSearchParams({
        stock_symbol: sentimentSymbol,
        start_date: startDate,
        end_date: endDate,
      });
      const res = await fetch(`http://localhost:8000/api/v1/sentiment/weekly?${params}`);
      if (!res.ok) throw new Error("API 호출 실패");
      const data = await res.json();
      setSentimentResult(data);
    } catch (e) {
      setSentimentError("감성점수 조회 중 오류 발생");
    } finally {
      setSentimentLoading(false);
    }
  };

  // 시황정보 조회 함수 추가
  const fetchMarketOverview = async () => {
    if (!startDate || !endDate) return alert("시작일과 종료일을 모두 입력하세요.");
    const res = await fetch(`http://localhost:8000/api/v1/market/overview?start_date=${startDate}&end_date=${endDate}`);
    const data = await res.json();
    setCompanyInfo({ ...companyInfo, market_overview: data });
  };

  // 연도 선택: 1999년부터 올해까지, 미래 연도는 선택 불가
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;
  const currentDay = new Date().getDate();
  const yearOptions = [];
  for (let y = 1999; y <= currentYear; y++) yearOptions.push(y);
  // 월 옵션: 올해라면 이번 달까지만, 과거라면 1~12월
  const monthOptions = (year === currentYear)
    ? Array.from({ length: currentMonth }, (_, i) => i + 1)
    : Array.from({ length: 12 }, (_, i) => i + 1);
  // 주차 옵션: 올해&이번달이면 오늘이 속한 주까지만, 그 외는 모두
  const filteredWeeks = (year === currentYear && month === currentMonth)
    ? validWeeks.filter(w => w.end <= today)
    : validWeeks;

  return (
    <div className="App">
      <h2>조회 기간 설정 (주차 단위)</h2>
      <div style={{ marginBottom: 16 }}>
        <select value={year} onChange={e => setYear(Number(e.target.value))} style={{ marginRight: 8 }}>
          {yearOptions.map(y => (
            <option key={y} value={y}>{y}년</option>
          ))}
        </select>
        <select value={month} onChange={e => setMonth(Number(e.target.value))} style={{ marginRight: 8 }}>
          {monthOptions.map(m => (
            <option key={m} value={m}>{m}월</option>
          ))}
        </select>
        <select value={selectedWeekIdx} onChange={e => setSelectedWeekIdx(Number(e.target.value))}>
          {filteredWeeks.map((w, idx) => (
            <option key={idx} value={idx}>{`${idx + 1}주차 (${w.start.getMonth() + 1}/${w.start.getDate()}~${w.end.getMonth() + 1}/${w.end.getDate()})`}</option>
          ))}
        </select>
      </div>

      <h2>고객 생성</h2>
      <input
        placeholder="고객 이름"
        value={customerName}
        onChange={(e) => setCustomerName(e.target.value)}
      />
      <input
        placeholder="PB 이름"
        value={pbName}
        onChange={(e) => setPbName(e.target.value)}
      />
      <input
        placeholder="투자 성향"
        value={investmentPropensity}
        onChange={(e) => setInvestmentPropensity(e.target.value)}
      />
      <div style={{ margin: '16px 0' }}>
        <b>포트폴리오 입력</b><br />
        <input
          placeholder="종목 (예: AAPL)"
          value={stockSymbolInput}
          onChange={e => setStockSymbolInput(e.target.value)}
          style={{ width: 80 }}
        />
        <input
          placeholder="수량"
          type="number"
          value={quantityInput}
          onChange={e => setQuantityInput(e.target.value)}
          style={{ width: 60 }}
        />
        <input
          placeholder="평균단가"
          type="number"
          value={priceInput}
          onChange={e => setPriceInput(e.target.value)}
          style={{ width: 100 }}
        />
        <button onClick={addPortfolioItem}>추가</button>
        <ul>
          {portfolioList.map((item, idx) => (
            <li key={idx}>
              {item.stock_symbol} / {item.quantity}주 / {item.average_purchase_price}원
              <button onClick={() => removePortfolioItem(idx)} style={{ marginLeft: 8 }}>삭제</button>
            </li>
          ))}
        </ul>
      </div>
      <button onClick={createCustomer}>고객 생성</button>
      {createdCustomer && <pre>{JSON.stringify(createdCustomer, null, 2)}</pre>}

      <h2>고객 목록 조회</h2>
      <button onClick={fetchCustomers}>고객 목록 불러오기</button>
      <pre>{JSON.stringify(customers, null, 2)}</pre>

      <h2>기업 정보 조회</h2>
      <input
        placeholder="예: AAPL"
        value={companySymbol}
        onChange={(e) => setCompanySymbol(e.target.value)}
      />
      <button onClick={fetchCompany} style={{ marginLeft: 8 }}>기업 정보 조회</button>
      {companyInfo && (
        <div style={{textAlign: 'left', maxWidth: 700, margin: '0 auto'}}>
          <h3>기업 개요</h3>
          <pre>{JSON.stringify({
            company_name: companyInfo.company_name,
            stock_symbol: companyInfo.stock_symbol,
            industry: companyInfo.industry,
            sector: companyInfo.sector,
            business_summary: companyInfo.business_summary,
            address: companyInfo.address
          }, null, 2)}</pre>
          <h3>SEC 재무제표</h3>
          <pre>{JSON.stringify(companyInfo.income_statements, null, 2)}</pre>
          <h3>주가/기술지표 (Stooq)</h3>
          <pre>{JSON.stringify(companyInfo.weekly_indicators, null, 2)}</pre>
          <h3>이동평균 (MA, Stooq)</h3>
          <pre>{JSON.stringify(companyInfo.moving_averages, null, 2)}</pre>
        </div>
      )}

      <h2>주가 예측 (고객 생성 후 클릭)</h2>
      <button onClick={createPrediction}>예측 요청</button>
      {predictionResult && <pre>{JSON.stringify(predictionResult, null, 2)}</pre>}

      <h2>보고서 생성 (고객+예측 생성 후 클릭)</h2>
      <button onClick={createReport}>보고서 생성</button>
      {reportResult && <pre>{JSON.stringify(reportResult, null, 2)}</pre>}

      <h2>주차별 감성점수 조회</h2>
      <div style={{ marginBottom: 16 }}>
        <input
          type="text"
          placeholder="기업명(심볼)"
          value={sentimentSymbol}
          onChange={e => setSentimentSymbol(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <button onClick={fetchSentimentScores} disabled={sentimentLoading}>
          {sentimentLoading ? "조회 중..." : "감성점수 조회"}
        </button>
      </div>
      {sentimentError && <div style={{ color: 'red' }}>{sentimentError}</div>}
      {typeof sentimentResult === 'number' && (
        <div style={{ fontWeight: 'bold', fontSize: 20, margin: '16px 0' }}>
          감성점수: {sentimentResult}
        </div>
      )}
      {sentimentResult && typeof sentimentResult !== 'number' && (
        <div>감성점수 데이터가 없습니다.</div>
      )}

      <h2>시황정보 조회</h2>
      <div style={{ marginBottom: 16 }}>
        <button onClick={fetchMarketOverview}>시황정보 조회</button>
      </div>
      {companyInfo && companyInfo.market_overview && (
        <div style={{textAlign: 'left', maxWidth: 700, margin: '0 auto'}}>
          <h3>미국 증시 지수</h3>
          <pre>{JSON.stringify(companyInfo.market_overview.us_stock_indices, null, 2)}</pre>
          <h3>미국 국채 금리</h3>
          <pre>{JSON.stringify(companyInfo.market_overview.us_treasury_yields, null, 2)}</pre>
          <h3>한국 환율</h3>
          <pre>{JSON.stringify(companyInfo.market_overview.kr_fx_rates, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
