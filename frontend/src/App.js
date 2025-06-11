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
  const [companyDate, setCompanyDate] = useState("");
  const [companyGranularity, setCompanyGranularity] = useState("year");

  // 감성점수 조회 관련 상태
  const [sentimentSymbol, setSentimentSymbol] = useState("");
  const [sentimentYear, setSentimentYear] = useState(new Date().getFullYear());
  const [sentimentMonth, setSentimentMonth] = useState(new Date().getMonth() + 1); // 1~12
  const [sentimentWeek, setSentimentWeek] = useState(1);
  const weeks = getWeeksOfMonth(sentimentYear, sentimentMonth);
  const selectedWeek = weeks.find(w => w.week === Number(sentimentWeek));
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
    if (companyDate) params.push(`date=${companyDate}`);
    if (companyGranularity) params.push(`granularity=${companyGranularity}`);
    if (params.length > 0) url += `?${params.join("&")}`;
    const res = await fetch(url);
    setCompanyInfo(await res.json());
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
    if (!sentimentSymbol || !selectedWeek) {
      setSentimentError("기업명, 연, 월, 주차를 모두 입력하세요.");
      return;
    }
    setSentimentLoading(true);
    setSentimentError("");
    setSentimentResult(null);
    try {
      const params = new URLSearchParams({
        stock_symbol: sentimentSymbol,
        start_date: selectedWeek.start.toISOString().slice(0, 10),
        end_date: selectedWeek.end.toISOString().slice(0, 10),
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

  return (
    <div className="App">
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
      <input
        type="date"
        value={companyDate}
        onChange={e => setCompanyDate(e.target.value)}
        style={{ marginLeft: 8 }}
      />
      <select
        value={companyGranularity}
        onChange={e => setCompanyGranularity(e.target.value)}
        style={{ marginLeft: 8 }}
      >
        <option value="day">일</option>
        <option value="month">월</option>
        <option value="year">연</option>
      </select>
      <button onClick={fetchCompany} style={{ marginLeft: 8 }}>기업 정보 조회</button>
      {companyInfo && <pre>{JSON.stringify(companyInfo, null, 2)}</pre>}

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
        <select value={sentimentYear} onChange={e => setSentimentYear(Number(e.target.value))} style={{ marginRight: 8 }}>
          {Array.from({ length: 6 }, (_, i) => 2022 + i).map(y => (
            <option key={y} value={y}>{y}년</option>
          ))}
        </select>
        <select value={sentimentMonth} onChange={e => setSentimentMonth(Number(e.target.value))} style={{ marginRight: 8 }}>
          {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
            <option key={m} value={m}>{m}월</option>
          ))}
        </select>
        <select value={sentimentWeek} onChange={e => setSentimentWeek(Number(e.target.value))} style={{ marginRight: 8 }}>
          {weeks.map(w => (
            <option key={w.week} value={w.week}>
              {`${w.week}주차 (${w.start.getMonth() + 1}-${w.start.getDate()}~${w.end.getMonth() + 1}-${w.end.getDate()})`}
            </option>
          ))}
        </select>
        <button onClick={fetchSentimentScores} disabled={sentimentLoading}>
          {sentimentLoading ? "조회 중..." : "감성점수 조회"}
        </button>
      </div>
      {sentimentError && <div style={{ color: 'red' }}>{sentimentError}</div>}
      {sentimentResult && (
        <table border="1" style={{ margin: '0 auto', minWidth: 300 }}>
          <thead>
            <tr>
              <th>주차 시작일</th>
              <th>감성점수</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(sentimentResult).map(([week, score]) => (
              <tr key={week}>
                <td>{week}</td>
                <td>{score.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;
