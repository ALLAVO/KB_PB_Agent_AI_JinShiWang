import React, { useState, useEffect } from "react";
import titlecloud from "../../assets/titlecloud.png";
import { fetchIndustryTop3Articles } from "../../api/industry";
import PipelineGraphSample from "./PipelineGraphSample";
import IndustryArticleList from "./IndustryArticleList";

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
              <IndustryArticleList articles={industryData.top3_articles} onArticleClick={handleArticleClick} />
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                해당 산업의 데이터가 없습니다.
              </div>
            )}
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

export default IndustryPipeline;
