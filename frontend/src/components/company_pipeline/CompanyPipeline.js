import React, { useState, useEffect } from 'react';
import StockPredictionCard from './StockPredictionCard';
import CompanyInfo from './CompanyInfo';
import titlecloud from '../../assets/titlecloud.png';
import { fetchTop3Articles } from '../../api/sentiment';
import { fetchWeeklySummaries } from '../../api/summarize';
import { fetchWeeklyKeywords } from '../../api/keyword';
import { fetchPredictionSummary } from '../../api/prediction';
import Top3Articles from './Top3Articles';
import ArticleDetailModal from './ArticleDetailModal';
// import StockChart from './StockChart';
// import './StockChart.css';
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
    
    // 리포트 제목 설정
    if (onSetReportTitle) {
      onSetReportTitle(`${cleanSymbol} 리포트`);
    }
    
    // 실제 API 호출 파라미터 확인
    console.log('API 호출', { symbol: cleanSymbol, startDate, endDate });
    try {
      // 네 API를 병렬로 호출 - cleanSymbol을 사용
      const [articlesData, summariesData, keywordsData, predictionData] = await Promise.all([
        fetchTop3Articles({ symbol: cleanSymbol, startDate, endDate }),
        fetchWeeklySummaries({ symbol: cleanSymbol, startDate, endDate }),
        fetchWeeklyKeywords({ symbol: cleanSymbol, startDate, endDate }),
        fetchPredictionSummary({ symbol: cleanSymbol, startDate, endDate })
      ]);
      setTop3Articles(articlesData);
      setSummaries(summariesData);
      setKeywords(keywordsData);
      setPrediction(predictionData);
      console.log('기사 데이터:', articlesData);
      console.log('요약 데이터:', summariesData);
      console.log('키워드 데이터:', keywordsData);
      console.log('예측 데이터:', predictionData);
    } catch (e) {
      console.error('API 호출 오류:', e);
      setError('데이터를 불러오지 못했습니다.');
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
            <img src={titlecloud} alt="cloud" /> {currentSymbol ? `${currentSymbol} 기업 정보` : '기업 정보'}
          </div>
          <CompanyInfo symbol={currentSymbol} />
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" /> {currentSymbol ? `${currentSymbol} 주가 동향` : '주가 동향'}
          </div>
          {/* 주가 차트 컴포넌트 추가 - currentSymbol 사용 */}
          
          {/* {currentSymbol && startDate && endDate && (
            <StockChart 
              symbol={currentSymbol}
              startDate={startDate}
              endDate={endDate}
            />
          )} */}
         
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
