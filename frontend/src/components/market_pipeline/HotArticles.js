import React, { useState, useEffect } from "react";
import titlecloud from "../../assets/titlecloud.png";
import { fetchMarketHotArticles } from "../../api/market";
import IndustryArticleList from "../industry_pipeline/IndustryArticleList";
import ArticleDetailModal from "../industry_pipeline/ArticleDetailModal";

function HotArticles({ year, month, weekStr, period, autoStart }) {
  const [started, setStarted] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [hotArticlesData, setHotArticlesData] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [showModal, setShowModal] = useState(false);
  
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

  // 자동 시작 트리거
  useEffect(() => {
    if (autoStart) {
      handleLoadHotArticles();
    }
  }, [autoStart, year, month, period]);

  const handleLoadHotArticles = async () => {
    setError("");
    setStarted(true);
    setLoading(true);
    setHotArticlesData(null);
    
    try {
      console.log('시장 핫 기사 API 호출', { startDate });
      const data = await fetchMarketHotArticles(startDate);
      setHotArticlesData(data);
      console.log('시장 핫 기사 데이터:', data);
    } catch (e) {
      console.error('시장 핫 기사 API 호출 오류:', e);
      setError('데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleStartReport = () => {
    handleLoadHotArticles();
  };

  return (
    <div>
      {!started && (
        <button
          className="report-start-btn"
          onClick={handleStartReport}
        >
          이 주 핫한 기사 TOP 3 보기
        </button>
      )}
      {started && (
        <>
          <div className="pipeline-title">
            <img src={titlecloud} alt="cloud" />이 주 핫한 기사 TOP 3
          </div>
          {/* 전 주에 핫한 기사 Top 3 섹션 */}
          <div className="industry-top3-section">
            {loading ? (
              <div className="industry-top3-loading">
                AI가 시장 트렌드를 분석하고 있습니다...
              </div>
            ) : error ? (
              <div className="industry-top3-error">
                {error}
              </div>
            ) : hotArticlesData && hotArticlesData.top3_articles && hotArticlesData.top3_articles.length > 0 ? (
              <IndustryArticleList articles={hotArticlesData.top3_articles} onArticleClick={handleArticleClick} />
            ) : (
              <div className="industry-top3-nodata">
                해당 기간의 데이터가 없습니다.
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

export default HotArticles;
