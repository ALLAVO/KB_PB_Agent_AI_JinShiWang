import React, { useState, useEffect } from 'react';
import StockChart from '../StockChart';
import titlecloud from '../../assets/titlecloud.png';
import { fetchTop3Articles } from '../../api/sentiment';
import { fetchWeeklySummaries } from '../../api/summarize';
import { fetchWeeklyKeywords } from '../../api/keyword';
import { fetchPredictionSummary } from '../../api/prediction';

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

  // 다음 주차 정보 계산
  const getNextWeekInfo = () => {
    const weekMatch = period.match(/\((\d+)주차\)/);
    if (weekMatch) {
      const currentWeek = parseInt(weekMatch[1]);
      const nextWeek = currentWeek + 1;
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
            <img src={titlecloud} alt="cloud" />기업 Pipeline
          </div>
          
          {/* 주가 차트 컴포넌트 추가 - currentSymbol 사용 */}
          {currentSymbol && startDate && endDate && (
            <StockChart 
              symbol={currentSymbol}
              startDate={startDate}
              endDate={endDate}
            />
          )}
          
          {/* 주가 전망 카드 - currentSymbol 사용 */}
          {started && (
            <div style={{
              marginTop: '24px',
              marginBottom: '16px',
              padding: '20px',
              backgroundColor: '#f8f9fa',
              borderRadius: '12px',
              border: '2px solid #e3f2fd',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '12px',
                gap: '8px'
              }}>
                <img 
                  src={require('../../assets/smile_king.png')} 
                  alt="smile_king" 
                  style={{
                    width: '24px',
                    height: '24px'
                  }}
                />
                <h3 style={{
                  margin: 0,
                  fontSize: '18px',
                  fontWeight: 'bold',
                  color: '#1976d2'
                }}>
                  {currentSymbol || '종목'} {getNextWeekInfo()} 주가 전망 한줄평
                </h3>
              </div>
              
              <div style={{
                fontSize: '15px',
                lineHeight: '1.6',
                color: '#333',
                backgroundColor: 'white',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #e0e0e0',
                minHeight: '60px',
                display: 'flex',
                alignItems: 'center'
              }}>
                {loading ? (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    color: '#666',
                    fontStyle: 'italic'
                  }}>
                    <span>🔄</span>
                    AI가 주가 전망을 분석하고 있습니다...
                  </div>
                ) : error && error !== '종목코드를 입력해주세요' ? (
                  <div style={{
                    color: '#d32f2f',
                    fontStyle: 'italic'
                  }}>
                    주가 전망 데이터를 불러오지 못했습니다.
                  </div>
                ) : prediction && prediction.summary ? (
                  prediction.summary
                ) : (
                  <div style={{
                    color: '#666',
                    fontStyle: 'italic'
                  }}>
                    주가 전망 데이터가 없습니다.
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* top3 기사 표시 */}
          <div className="top3-articles">
            <b>Top3 기사:</b>
            {loading ? '로딩 중...'
              : error && error !== '종목코드를 입력해주세요'
                ? error
              : top3Articles && top3Articles.top3_articles && top3Articles.top3_articles.length > 0 ? (
                <ol style={{marginTop: '8px'}}>
                  {top3Articles.top3_articles.map((art, idx) => (
                    <li key={idx} style={{marginBottom: '12px'}}>
                      <div style={{fontWeight:'bold', fontSize:'16px'}}>
                        {art.article_title}
                        <span style={{marginLeft:'10px', color:'#0077cc', fontWeight:'normal', fontSize:'15px'}}>
                          {art.score > 0 ? '+' : ''}{art.score}
                        </span>
                      </div>
                      {/* 기사 작성 날짜 - 작은 회색 글씨로 표시 */}
                      <div style={{fontSize:'12px', color:'#888', marginBottom:'2px'}}>{art.date}</div>
                      
                      {/* 기사 키워드 - 해시태그 형태로 표시 */}
                      {(() => {
                        const articleKeywords = findKeywordsForArticle(art);
                        return articleKeywords && articleKeywords.length > 0 ? (
                          <div style={{
                            margin: '6px 0',
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '4px'
                          }}>
                            {articleKeywords.slice(0, 5).map((keyword, idx) => (
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
                        ) : loading ? (
                          <div style={{
                            fontSize: '11px',
                            color: '#9e9e9e',
                            fontStyle: 'italic',
                            margin: '6px 0'
                          }}>
                            키워드 생성 중...
                          </div>
                        ) : null;
                      })()}
                      
                      {/* 기사 요약 내용 */}
                      {(() => {
                        const summary = findSummaryForArticle(art);
                        return summary ? (
                          <div style={{
                            fontSize: '13px',
                            color: '#555',
                            backgroundColor: '#f8f9fa',
                            padding: '8px 12px',
                            borderRadius: '6px',
                            border: '1px solid #e9ecef',
                            margin: '6px 0',
                            lineHeight: '1.4'
                          }}>
                            <div style={{fontWeight: 'bold', fontSize: '12px', color: '#6c757d', marginBottom: '4px'}}>
                              📄 기사 요약
                            </div>
                            {summary}
                          </div>
                        ) : loading ? (
                          <div style={{
                            fontSize: '12px',
                            color: '#6c757d',
                            fontStyle: 'italic',
                            margin: '6px 0'
                          }}>
                            요약 생성 중...
                          </div>
                        ) : null;
                      })()}
                      
                      {/* 기사 본문 확인 버튼 */}
                      <button 
                        onClick={() => handleArticleClick(art)}
                        style={{
                          backgroundColor: '#0077cc',
                          color: 'white',
                          border: 'none',
                          padding: '6px 12px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          cursor: 'pointer',
                          marginTop: '4px'
                        }}
                      >
                        기사 본문 자세히 확인하기
                      </button>
                    </li>
                  ))}
                </ol>
              ) : '데이터 없음'}
          </div>
          
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
                {/* 닫기 버튼 */}
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
                
                {/* 모달 내용 */}
                <div style={{marginRight: '30px'}}>
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

export default CompanyPipeline;
