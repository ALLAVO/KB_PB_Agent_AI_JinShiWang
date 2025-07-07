import React from 'react';

function Top3Articles({ loading, error, top3Articles, findKeywordsForArticle, findSummaryForArticle, handleArticleClick }) {
  return (
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
  );
}

export default Top3Articles;
