import React, { useState, useEffect } from "react";
import titlecloud from "../../assets/titlecloud.png";
import { fetchIndustryTop3Articles } from "../../api/industry";
import IndustryArticleList from "./IndustryArticleList";
import ArticleDetailModal from "./ArticleDetailModal";

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
  
  // period에서 주차 시작일 및 종료일 추출
  const dateMatch = period.match(/(\d{2})\.(\d{2}) - (\d{2})\.(\d{2})/);
  let startDate = null;
  let endDate = null;
  if (dateMatch) {
    const y = year;
    startDate = `${y}-${dateMatch[1]}-${dateMatch[2]}`;
    endDate = `${y}-${dateMatch[3]}-${dateMatch[4]}`;
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
      console.log('산업 API 호출', { sector: categoryToUse.trim(), endDate });
      const data = await fetchIndustryTop3Articles({ 
        sector: categoryToUse.trim(), 
        endDate: endDate 
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
    // 버튼 클릭 시 바로 리포트 출력
    handleSearch(sector, false);
  };

  useEffect(() => {
    if (!started && onSetReportTitle) {
      onSetReportTitle('산업 리포트');
    }
    // eslint-disable-next-line
  }, [started]);

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString();
  };

  const formatPercentage = (num) => {
    if (num === null || num === undefined) return 'N/A';
    const sign = num >= 0 ? '+' : '';
    return `${sign}${num.toFixed(2)}%`;
  };

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
            <img src={titlecloud} alt="cloud" />{inputSymbol} 산업 핵심 기업
          </div>

          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" />{inputSymbol} 산업 핵심 뉴스
          </div>
          {/* 전 주에 핫한 기사 Top 3 섹션 */}
          <div className="industry-top3-section">
            {loading ? (
              <div className="industry-top3-loading">
                AI가 산업 트렌드를 분석하고 있습니다...
              </div>
            ) : error && error !== '산업군 이름을 입력해주세요' ? (
              <div className="industry-top3-error">
                {error}
              </div>
            ) : industryData && industryData.top3_articles && industryData.top3_articles.length > 0 ? (
              <IndustryArticleList articles={industryData.top3_articles} onArticleClick={handleArticleClick} />
            ) : (
              <div className="industry-top3-nodata">
                해당 산업의 데이터가 없습니다.
              </div>
            )}
          </div>
          
          {/* 기사 상세 모달 */}
          <ArticleDetailModal article={showModal && selectedArticle} onClose={closeModal} />
        </>
      )}
    </div>
  );
}

export default IndustryPipeline;
