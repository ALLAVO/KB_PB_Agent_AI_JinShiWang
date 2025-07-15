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
import { fetchCompanyInfo } from '../../api/company';
import { fetchCombinedStockChart, fetchStockChartSummary, fetchEnhancedStockInfo } from '../../api/stockChart';
import Top3Articles from './Top3Articles';
import ArticleDetailModal from './ArticleDetailModal';
import StockChart from './StockChart';
import ReturnAnalysisChart from './ReturnAnalysisChart';
import './StockChart.css';
import './Top3Articles.css';

function CompanyPipeline({ year, month, weekStr, period, onSetReportTitle, autoCompanySymbol, autoCompanyTrigger, onAutoCompanyDone }) {
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
  const [companyInfo, setCompanyInfo] = useState(null);
  const [stockChartData, setStockChartData] = useState(null);
  const [stockChartSummary, setStockChartSummary] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [currentSymbol, setCurrentSymbol] = useState(""); // 현재 처리 중인 심볼 저장

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

  const handleSearch = async (overrideSymbol, isAuto) => {
    setStarted(true); // 버튼 클릭 시 바로 started 상태로 전환
    const symbolToUse = overrideSymbol !== undefined ? overrideSymbol : inputSymbol;
    
    // symbol 값을 문자열로 변환하고 trim 처리
    const cleanSymbol = typeof symbolToUse === 'string' ? symbolToUse.trim() : String(symbolToUse || '').trim();
    
    if (!cleanSymbol) {
      setError('종목코드를 입력해주세요');
      return;
    }
    
    // 현재 처리 중인 심볼 저장
    setCurrentSymbol(cleanSymbol);
    setLoading(true);
    setError("");
    setTop3Articles(null);
    setSummaries(null);
    setKeywords(null);
    setPrediction(null);
    setFinancialMetrics(null);
    setValuationMetrics(null);
    setCompanyInfo(null);
    setStockChartData(null);
    setStockChartSummary(null);
    
    // 리포트 제목 설정
    if (onSetReportTitle) {
      onSetReportTitle(`${cleanSymbol} 리포트`);
    }
    
    // 실제 API 호출 파라미터 확인
    console.log('🚀 API 호출 시작', { symbol: cleanSymbol, startDate, endDate });
    try {
      // 렌더링 순서에 맞춰 API 호출 순서도 변경
      const fixedChartTypes = ['price', 'volume'];
      
      console.log('📞 1. Company Info API 호출...');
      const companyInfoData = await fetchCompanyInfo(cleanSymbol);
      console.log('✅ Company Info 완료:', companyInfoData);

      console.log('📞 2. Financial Metrics API 호출...');
      const financialData = await fetchFinancialMetrics({ symbol: cleanSymbol, endDate });
      console.log('✅ Financial Metrics 완료:', financialData);

      console.log('📞 3. Valuation Metrics API 호출...');
      const valuationData = await fetchValuationMetrics({ symbol: cleanSymbol, endDate });
      console.log('✅ Valuation Metrics 완료:', valuationData);

      console.log('📞 4. Stock Chart Data API 호출...');
      const stockChartDataResponse = await fetchCombinedStockChart(cleanSymbol, startDate, endDate, fixedChartTypes);
      console.log('✅ Stock Chart Data 완료:', stockChartDataResponse);

      console.log('📞 5. Stock Chart Summary API 호출...');
      const stockChartSummaryResponse = await fetchStockChartSummary(cleanSymbol, startDate, endDate);
      console.log('✅ Stock Chart Summary 완료:', stockChartSummaryResponse);

      console.log('📞 6. Enhanced Stock Info API 호출...');
      const enhancedStockInfoResponse = await fetchEnhancedStockInfo(cleanSymbol);
      console.log('✅ Enhanced Stock Info 완료:', enhancedStockInfoResponse);

      console.log('📞 7. Prediction Summary API 호출...');
      const predictionData = await fetchPredictionSummary({ symbol: cleanSymbol, startDate, endDate });
      console.log('✅ Prediction Summary 완료:', predictionData);

      console.log('📞 8. Top3 Articles API 호출...');
      const articlesData = await fetchTop3Articles({ symbol: cleanSymbol, startDate, endDate });
      console.log('✅ Top3 Articles 완료:', articlesData);

      console.log('📞 9. Weekly Summaries API 호출...');
      const summariesData = await fetchWeeklySummaries({ symbol: cleanSymbol, startDate, endDate });
      console.log('✅ Weekly Summaries 완료:', summariesData);

      console.log('📞 10. Weekly Keywords API 호출...');
      const keywordsData = await fetchWeeklyKeywords({ symbol: cleanSymbol, startDate, endDate });
      console.log('✅ Weekly Keywords 완료:', keywordsData);
      
      console.log('🎯 모든 API 호출 완료! 데이터 처리 시작...');
      
      // 차트 데이터 변환
      const transformedChartData = stockChartDataResponse.dates.map((date, index) => {
        const item = { date };
        
        // 주가 데이터
        if (stockChartDataResponse.data.price) {
          item.close = stockChartDataResponse.data.price.closes[index];
          item.open = stockChartDataResponse.data.price.opens[index];
          item.high = stockChartDataResponse.data.price.highs[index];
          item.low = stockChartDataResponse.data.price.lows[index];
        }
        
        // 거래량 데이터
        if (stockChartDataResponse.data.volume) {
          item.volume = stockChartDataResponse.data.volume.volumes[index];
        }
        
        return item;
      });
      
      // 상세 정보를 요약 정보에 병합
      const mergedChartSummary = {
        ...stockChartSummaryResponse,
        ...enhancedStockInfoResponse
      };
      
      // 실제로 사용하는 데이터만 setState
      console.log('📊 상태 업데이트 시작...');
      setCompanyInfo(companyInfoData);
      setFinancialMetrics(financialData);
      setValuationMetrics(valuationData);
      setStockChartData(transformedChartData);
      setStockChartSummary(mergedChartSummary);
      setPrediction(predictionData);
      setTop3Articles(articlesData);
      setSummaries(summariesData);
      setKeywords(keywordsData);
      
      console.log('🎉 모든 데이터 상태 업데이트 완료!');
      console.log('📋 최종 데이터 요약:');
      console.log('   기업 정보:', companyInfoData ? '✅' : '❌');
      console.log('   재무지표:', financialData ? '✅' : '❌');
      console.log('   벨류에이션:', valuationData ? '✅' : '❌');
      console.log('   주가 차트:', transformedChartData ? '✅' : '❌');
      console.log('   예측 데이터:', predictionData ? '✅' : '❌');
      console.log('   기사 데이터:', articlesData ? '✅' : '❌');
      console.log('   요약 데이터:', summariesData ? '✅' : '❌');
      console.log('   키워드 데이터:', keywordsData ? '✅' : '❌');
    } catch (e) {
      console.error('❌ API 호출 오류:', e);
      console.error('❌ 오류 상세:', {
        message: e.message,
        stack: e.stack,
        name: e.name
      });
      setError(`데이터를 불러오지 못했습니다: ${e.message}`);
    } finally {
      setLoading(false);
      if (isAuto && onAutoCompanyDone) {
        onAutoCompanyDone();
      }
    }
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
      {started && (
        <>
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" /> {currentSymbol ? `기업 정보` : '기업 정보'}
          </div>
          <CompanyInfo symbol={currentSymbol} companyData={companyInfo} loading={loading} error={error} />
          
          <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start', marginBottom: '24px' }}>
            <div style={{ flex: 1 }}>
              <div className="pipeline-title">
                <img src={titlecloud} alt="cloud" /> {currentSymbol ? `재무지표` : '재무지표'}
              </div>
              <FinancialMetrics 
                loading={loading}
                error={error}
                financialMetrics={financialMetrics}
              />
            </div>
            <div style={{ flex: 1 }}>
              <div className="pipeline-title">
                <img src={titlecloud} alt="cloud" /> {currentSymbol ? `벨류에이션 지표` : '벨류에이션 지표'}
              </div>
              <ValuationMetrics 
                loading={loading}
                error={error}
                valuationMetrics={valuationMetrics}
              />
            </div>
          </div>
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" /> {currentSymbol ? `주가 동향` : '주가 동향'}
          </div>
          {/* 주가 차트 컴포넌트 추가 - currentSymbol 사용 */}
          
          {currentSymbol && startDate && endDate && (
            <StockChart 
              symbol={currentSymbol}
              startDate={startDate}
              endDate={endDate}
              chartData={stockChartData}
              chartSummary={stockChartSummary}
              loading={loading}
              error={error}
            />
          )}
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" /> {currentSymbol ? `지수 대비 수익률 분석` : '지수 대비 수익률 분석'}
          </div>
          {/* 주가 차트 아래에 ReturnAnalysisChart 분리 렌더링 */}
          {currentSymbol && startDate && endDate && (
            <ReturnAnalysisChart 
              symbol={currentSymbol}
              startDate={startDate}
              endDate={endDate}
            />
          )}
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" /> {` ${getNextWeekInfo()} 진시황의 혜안`}
          </div>
          {/* 주가 전망 카드 - currentSymbol 사용 */}
          {started && (
            <StockPredictionCard 
              currentSymbol={currentSymbol}
              getNextWeekInfo={getNextWeekInfo}
              loading={loading}
              error={error}
              prediction={prediction}
            />
          )}
          <div className="pipeline-title" style={{ marginBottom: '8px' }}>
            <img src={titlecloud} alt="cloud" /> {`${getCurrentWeekInfo()} 핵심 뉴스`}
          </div>
          {/* top3 기사 표시 */}
          <Top3Articles
            loading={loading}
            error={error}
            top3Articles={top3Articles}
            findKeywordsForArticle={findKeywordsForArticle}
            findSummaryForArticle={findSummaryForArticle}
            handleArticleClick={handleArticleClick}
          />
          <div style={{ background: '#fff', height: '50px', width: '100%', borderRadius: '8px', marginTop: '24px' }} />
          {/* 기사 상세 모달 */}
          <ArticleDetailModal show={showModal} article={selectedArticle} onClose={closeModal} />
        </>
      )}
    </div>
  );
}

export default CompanyPipeline;
