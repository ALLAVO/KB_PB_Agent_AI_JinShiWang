import React, { useState, useEffect } from 'react';
import StockPredictionCard from './StockPredictionCard';
import CompanyInfo from './CompanyInfo';
import FinancialMetrics from './FinancialMetrics';
import ValuationMetrics from './ValuationMetrics';
import titlecloud from '../../assets/titlecloud.png';
import { fetchTop3Articles } from '../../api/sentiment';
import { fetchWeeklySummaries } from '../../api/summarize';
import { fetchWeeklyKeywords } from '../../api/keyword';
import { fetchPredictionSummary } from '../../api/prediction';
import { fetchFinancialMetrics } from '../../api/financialMetrics';
import { fetchValuationMetrics } from '../../api/valuation';
import { fetchCompanySector } from '../../api/companySector';
import Top3Articles from './Top3Articles';
import ArticleDetailModal from './ArticleDetailModal';
import StockChart from './StockChart';
import ReturnAnalysisChart from './ReturnAnalysisChart';
import { fetchCombinedStockChart, fetchStockChartSummary, fetchEnhancedStockInfo } from '../../api/stockChart';
import { fetchCombinedReturnChart } from '../../api/returnAnalysis';
import './StockChart.css';
import './Top3Articles.css';

function CompanyPipeline({ year, month, weekStr, period, onSetReportTitle, autoCompanySymbol, autoCompanyTrigger, onAutoCompanyDone, onIndustryClick, onMarketClick }) {
  const [started, setStarted] = useState(false);
  const [inputSymbol, setInputSymbol] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [top3Articles, setTop3Articles] = useState(null);
  const [summaries, setSummaries] = useState(null);
  const [keywords, setKeywords] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [financialMetrics, setFinancialMetrics] = useState(null);
  const [valuationMetrics, setValuationMetrics] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [currentSymbol, setCurrentSymbol] = useState(""); // 현재 처리 중인 심볼 저장
  const [companyData, setCompanyData] = useState(null);
  const [companyLoading, setCompanyLoading] = useState(false);
  const [companyError, setCompanyError] = useState("");
  const [chartData, setChartData] = useState([]);
  const [chartSummary, setChartSummary] = useState(null);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartError, setChartError] = useState("");
  const [returnChartData, setReturnChartData] = useState([]);
  const [returnTableData, setReturnTableData] = useState(null);
  const [returnLoading, setReturnLoading] = useState(false);
  const [returnError, setReturnError] = useState("");
  const [selectedPeriod, setSelectedPeriod] = useState('6M');
  // 섹터 정보 상태 추가
  const [companySector, setCompanySector] = useState(null);
  const [sectorLoading, setSectorLoading] = useState(false);
  const [sectorError, setSectorError] = useState("");

  // 섹션별 로딩/에러 상태 추가
  const [section1Loading, setSection1Loading] = useState(false);
  const [section1Error, setSection1Error] = useState("");
  const [section2Loading, setSection2Loading] = useState(false);
  const [section2Error, setSection2Error] = useState("");
  const [section3Loading, setSection3Loading] = useState(false);
  const [section3Error, setSection3Error] = useState("");

  const textSummary = `${year}년 ${month}월 ${weekStr} 기업 데이터 분석 요약입니다.`;

  // period에서 주차 시작일, 종료일 추출 (예: "12.10 - 12.16 (1주차)")
  const dateMatch = period.match(/(\d{2})\.(\d{2}) - (\d{2})\.(\d{2})/);
  let startDate = null;
  let endDate = null;
  if (dateMatch) {
    const y = year;
    startDate = `${y}-${dateMatch[1]}-${dateMatch[2]}`;
    endDate = `${y}-${dateMatch[3]}-${dateMatch[4]}`;
  }

  // 이번 주차 정보 계산
  const getCurrentWeekInfo = () => {
    const weekMatch = period.match(/\((\d+)주차\)/);
    if (weekMatch) {
      const currentWeek = parseInt(weekMatch[1]);
      return `${month}월 ${currentWeek}주차`;
    }
    return "이번 주차";
  };

  // 다음 주차 정보 계산
  const getNextWeekInfo = () => {
    const weekMatch = period.match(/\((\d+)주차\)/);
    if (weekMatch) {
      const nextWeek = parseInt(weekMatch[1]) + 1;
      return `${month}월 ${nextWeek}주차`;
    }
    return "다음 주차";
  };

  const handleArticleClick = (article) => {
    setSelectedArticle(article);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedArticle(null);
  };

  // 특정 기사의 요약을 찾는 함수
  const findSummaryForArticle = (article) => {
    if (!summaries) return null;
    
    try {
      // summaries는 주차별로 구성되어 있음: { "2023-12-10": [summary1, summary2, summary3], ... }
      for (const weekData of Object.values(summaries)) {
        if (!Array.isArray(weekData)) continue;
        
        const summary = weekData.find(s => {
          if (!s) return false;
          // 날짜와 기사 제목으로 매칭 (더 안전함)
          const dateMatch = s.date === article.date;
          const titleMatch = s.article_title === article.article_title;
          return dateMatch && titleMatch;
        });
        
        if (summary && summary.summary) {
          return summary.summary;
        }
      }
    } catch (error) {
      console.error('요약 찾기 오류:', error);
    }
    
    return null;
  };

  // 특정 기사의 키워드를 찾는 함수
  const findKeywordsForArticle = (article) => {
    if (!keywords) return null;
    
    try {
      // keywords는 주차별로 구성되어 있음: { "2023-12-10": [keyword1, keyword2, keyword3], ... }
      for (const weekData of Object.values(keywords)) {
        if (!Array.isArray(weekData)) continue;
        
        const keywordData = weekData.find(k => {
          if (!k) return false;
          // 날짜와 기사 제목으로 매칭
          const dateMatch = k.date === article.date;
          const titleMatch = k.article_title === article.article_title;
          return dateMatch && titleMatch;
        });
        
        if (keywordData && keywordData.keywords) {
          return keywordData.keywords;
        }
      }
    } catch (error) {
      console.error('키워드 찾기 오류:', error);
    }
    
    return null;
  };

  // 섹션별 API 호출 함수
  const fetchSection1 = async (symbol) => {
    setSection1Loading(true);
    setSection1Error("");
    setCompanyLoading(true);
    setSectorLoading(true);
    try {
      const [companyRes, financialData, valuationData, sectorData] = await Promise.all([
        fetch(`/api/v1/companies/${symbol}/info`).then(res => {
          if (!res.ok) throw new Error('기업 정보를 불러오는데 실패했습니다.');
          return res.json();
        }),
        fetchFinancialMetrics({ symbol, endDate }),
        fetchValuationMetrics({ symbol, endDate }),
        fetchCompanySector(symbol).catch(err => {
          console.warn('섹터 정보 로드 실패:', err);
          return null;
        })
      ]);
      setCompanyData(companyRes);
      setFinancialMetrics(financialData);
      setValuationMetrics(valuationData);
      setCompanySector(sectorData);
    } catch (e) {
      setSection1Error(e.message || '섹션1 데이터를 불러오지 못했습니다.');
      setCompanyError(e.message || '기업 정보를 불러오지 못했습니다.');
    } finally {
      setSection1Loading(false);
      setCompanyLoading(false);
      setSectorLoading(false);
    }
  };

  const fetchSection2 = async (symbol) => {
    setSection2Loading(true);
    setSection2Error("");
    setChartLoading(true);
    setReturnLoading(true);
    try {
      // 기간 계산 (차트)
      const end = new Date(endDate);
      const start = new Date(end);
      switch (selectedPeriod) {
        case '1W': start.setDate(end.getDate() - 7); break;
        case '1M': start.setMonth(end.getMonth() - 1); break;
        case '3M': start.setMonth(end.getMonth() - 3); break;
        case '6M': start.setMonth(end.getMonth() - 6); break;
        case '1Y': start.setFullYear(end.getFullYear() - 1); break;
        default: start.setMonth(end.getMonth() - 1);
      }
      const calcStartDate = start.toISOString().split('T')[0];
      const calcEndDate = end.toISOString().split('T')[0];
      const fixedChartTypes = ['price', 'volume'];
      // 18개월 고정 기간 (수익률)
      const startReturn = new Date(end);
      startReturn.setMonth(end.getMonth() - 18);
      const calcReturnStartDate = startReturn.toISOString().split('T')[0];
      // 병렬 호출
      const [chartRes, chartSummaryRes, enhancedRes, returnRes] = await Promise.all([
        fetchCombinedStockChart(symbol, calcStartDate, calcEndDate, fixedChartTypes),
        fetchStockChartSummary(symbol, calcStartDate, calcEndDate),
        fetchEnhancedStockInfo(symbol),
        fetchCombinedReturnChart(symbol, calcReturnStartDate, calcEndDate)
      ]);
      // 차트 데이터 변환
      const transformedData = chartRes.dates.map((date, index) => {
        const item = { date };
        if (chartRes.data.price) {
          item.close = chartRes.data.price.closes[index];
          item.open = chartRes.data.price.opens[index];
          item.high = chartRes.data.price.highs[index];
          item.low = chartRes.data.price.lows[index];
        }
        if (chartRes.data.volume) {
          item.volume = chartRes.data.volume.volumes[index];
        }
        return item;
      });
      setChartData(transformedData);
      setChartSummary({ ...chartSummaryRes, ...enhancedRes });
      // 수익률 데이터 변환
      const sixMonthsAgo = new Date(endDate);
      sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
      const sixMonthsAgoStr = sixMonthsAgo.toISOString().split('T')[0];
      const transformedReturnData = returnRes.chart_data.dates
        .map((date, index) => ({
          date,
          stock_index: returnRes.chart_data.stock_index[index],
          benchmark_index: returnRes.chart_data.sp500_index[index]
        }))
        .filter(item => item.date >= sixMonthsAgoStr);
      setReturnChartData(transformedReturnData);
      setReturnTableData(returnRes.table_data);
    } catch (e) {
      setSection2Error(e.message || '섹션2 데이터를 불러오지 못했습니다.');
      setChartError(e.message || '차트 데이터를 불러오지 못했습니다.');
      setReturnError(e.message || '수익률 데이터를 불러오지 못했습니다.');
    } finally {
      setSection2Loading(false);
      setChartLoading(false);
      setReturnLoading(false);
    }
  };

  const fetchSection3 = async (symbol) => {
    setSection3Loading(true);
    setSection3Error("");
    setLoading(true);
    try {
      const [predictionRes, articlesRes, summariesRes, keywordsRes] = await Promise.all([
        fetchPredictionSummary({ symbol, startDate, endDate }),
        fetchTop3Articles({ symbol, startDate, endDate }),
        fetchWeeklySummaries({ symbol, startDate, endDate }),
        fetchWeeklyKeywords({ symbol, startDate, endDate })
      ]);
      setPrediction(predictionRes);
      setTop3Articles(articlesRes);
      setSummaries(summariesRes);
      setKeywords(keywordsRes);
    } catch (e) {
      setSection3Error(e.message || '섹션3 데이터를 불러오지 못했습니다.');
      setError(e.message || '데이터를 불러오지 못했습니다.');
    } finally {
      setSection3Loading(false);
      setLoading(false);
      if (onAutoCompanyDone) onAutoCompanyDone();
    }
  };

  // 전체 검색 핸들러
  const handleSearch = async (overrideSymbol, isAuto) => {
    setStarted(true);
    const symbolToUse = overrideSymbol !== undefined ? overrideSymbol : inputSymbol;
    const cleanSymbol = typeof symbolToUse === 'string' ? symbolToUse.trim() : String(symbolToUse || '').trim();
    if (!cleanSymbol) {
      setError('종목코드를 입력해주세요');
      return;
    }
    setCurrentSymbol(cleanSymbol);
    setError("");
    setCompanyData(null);
    setFinancialMetrics(null);
    setValuationMetrics(null);
    setChartData([]);
    setChartSummary(null);
    setReturnChartData([]);
    setReturnTableData(null);
    setPrediction(null);
    setTop3Articles(null);
    setSummaries(null);
    setKeywords(null);
    setCompanySector(null);
    setCompanyError("");
    setChartError("");
    setReturnError("");
    setSectorError("");
    setSection1Error("");
    setSection2Error("");
    setSection3Error("");
    if (onSetReportTitle) {
      onSetReportTitle(`${cleanSymbol} 리포트`);
    }
    await fetchSection1(cleanSymbol);
    await fetchSection2(cleanSymbol);
    await fetchSection3(cleanSymbol);
  };

  // 자동 입력 및 자동 검색 트리거
  useEffect(() => {
    if (autoCompanyTrigger && autoCompanySymbol) {
      // autoCompanySymbol을 문자열로 변환하여 설정
      const cleanAutoSymbol = typeof autoCompanySymbol === 'string' ? autoCompanySymbol.trim() : String(autoCompanySymbol || '').trim();
      console.log('자동 심볼 설정:', cleanAutoSymbol); // 디버깅용
      setInputSymbol(cleanAutoSymbol);
      setTimeout(() => {
        handleSearch(cleanAutoSymbol, true);
      }, 200);
    }
    // eslint-disable-next-line
  }, [autoCompanyTrigger, autoCompanySymbol]);

  useEffect(() => {
    if (!started && onSetReportTitle) {
      onSetReportTitle('기업 리포트');
    }
    // eslint-disable-next-line
  }, [started]);

  return (
    <div>
      {!started && (
        <div className="company-search-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          <label style={{marginBottom: 0}}>
            <input
              type="text"
              value={inputSymbol}
              onChange={e => {
                const value = e.target.value;
                setInputSymbol(typeof value === 'string' ? value : String(value || ''));
                if (error) setError("");
              }}
              className="company-symbol-input center-text"
              placeholder="종목코드를 입력해주세요."
            />
          </label>
          <button className="company-search-btn" onClick={() => handleSearch()}>리포트 출력</button>
        </div>
      )}
      {/* 전체 덮는 로딩 화면: 처음 검색 시 section1Loading && !companyData */}
      {started && section1Loading && !companyData && (
        <div className="industry-loading-message">
          기업 데이터를 불러오는 중...
        </div>
      )}
      {/* 기존 섹션별 로딩 화면: section1Loading && companyData (또는 section1Loading만) */}
      {started && (!section1Loading || companyData) && (
        <>
          {/* 섹션1: 기업 정보, 재무지표, 벨류에이션 지표 */}
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" /> {currentSymbol ? `기업 정보` : '기업 정보'}
          </div>
          {section1Loading ? (
            <div className="company-loading-message" style={{ textAlign: 'center', margin: '32px 0' }}>
              기업 데이터를 불러오는 중...
            </div>
          ) : (
            <>
              <CompanyInfo 
                companyData={companyData}
                loading={section1Loading}
                error={section1Error || companyError}
                onIndustryClick={onIndustryClick}
                companySector={companySector}
              />
              <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start', marginBottom: '24px', marginTop : '16px' }}>
                <div style={{ flex: 1 }}>
                  <div className="pipeline-title">
                    <img src={titlecloud} alt="cloud" /> {currentSymbol ? `재무지표` : '재무지표'}
                  </div>
                  <FinancialMetrics 
                    loading={section1Loading}
                    error={section1Error}
                    financialMetrics={financialMetrics}
                  />
                </div>
                <div style={{ flex: 1}}>
                  <div className="pipeline-title">
                    <img src={titlecloud} alt="cloud" /> {currentSymbol ? `벨류에이션 지표` : '벨류에이션 지표'}
                  </div>
                  <ValuationMetrics 
                    loading={section1Loading}
                    error={section1Error}
                    valuationMetrics={valuationMetrics}
                  />
                </div>
              </div>
            </>
          )}
          {/* 섹션2: 주가 차트, 수익률 차트 */}
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" /> {currentSymbol ? `주가 동향` : '주가 동향'}
          </div>
          {section1Loading ? (
            <div className="company-loading-message" style={{ textAlign: 'center', margin: '32px 0' }}>
              주가 및 수익률 데이터를 불러오는 중...
            </div>
          ) : (
            <>
              {currentSymbol && startDate && endDate && (
                <StockChart 
                  chartData={chartData}
                  chartSummary={chartSummary}
                  loading={section2Loading}
                  error={section2Error || chartError}
                  selectedPeriod={selectedPeriod}
                  onPeriodChange={setSelectedPeriod}
                />
              )}
              <div className="pipeline-title">
                <img src={titlecloud} alt="cloud" /> 
                <span>지수 대비 수익률 분석</span>
                {onMarketClick && (
                  <span 
                    onClick={onMarketClick}
                    style={{
                      marginLeft: '12px',
                      color: '#B8A48A', // 더 연한 색상
                      cursor: 'pointer',
                      textDecoration: 'underline',
                      fontSize: '16px', // 더 큰 글씨
                      fontWeight: 'normal',
                      transition: 'color 0.2s ease'
                    }}
                    title="증시 분석으로 이동"
                    onMouseEnter={(e) => {
                      e.target.style.color = '#D2C2B0'; // hover 시 더 연하게
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.color = '#B8A48A';
                    }}
                  >
                    (더 알아보기)
                  </span>
                )}
              </div>
              {currentSymbol && startDate && endDate && (
                <ReturnAnalysisChart 
                  chartData={returnChartData}
                  tableData={returnTableData}
                  loading={section2Loading}
                  error={section2Error || returnError}
                  symbol={currentSymbol}
                />
              )}
            </>
          )}
          {/* 섹션3: 주가 전망 카드, top3 기사 */}
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" /> {` ${getNextWeekInfo()} 진시황의 혜안`}
          </div>
          {section1Loading ? (
            <div className="company-loading-message" style={{ textAlign: 'center', margin: '32px 0' }}>
              기업 핵심 뉴스 데이터를 불러오는 중...
            </div>
          ) : (
            <>
              {started && (
                <StockPredictionCard 
                  currentSymbol={currentSymbol}
                  getNextWeekInfo={getNextWeekInfo}
                  loading={section3Loading || (!top3Articles && !section3Error)}
                  error={section3Error || error}
                  prediction={prediction}
                />
              )}
              <div className="pipeline-title" style={{ marginBottom: '8px' }}>
                <img src={titlecloud} alt="cloud" /> {`${getCurrentWeekInfo()} 핵심 뉴스`}
              </div>
              <Top3Articles
                loading={section3Loading || (!top3Articles && !section3Error)}
                error={section3Error || error}
                top3Articles={top3Articles}
                findKeywordsForArticle={findKeywordsForArticle}
                findSummaryForArticle={findSummaryForArticle}
                handleArticleClick={handleArticleClick}
              />
              <div style={{ background: '#fff', height: '50px', width: '100%', borderRadius: '8px', marginTop: '24px' }} />
              <ArticleDetailModal show={showModal} article={selectedArticle} onClose={closeModal} />
            </>
          )}
        </>
      )}
    </div>
  );
}

export default CompanyPipeline;
