import React from "react";

function IndustryArticleList({ articles, onArticleClick }) {
  return (
    <ol style={{ marginTop: '8px' }}>
      {articles.map((art, idx) => (
        <li key={idx} style={{ marginBottom: '20px', padding: '16px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #e9ecef' }}>
          {/* 기사 제목 */}
          <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '12px' }}>
            {art.article_title}
            <span style={{ marginLeft: '10px', color: '#0077cc', fontWeight: 'normal', fontSize: '14px' }}>
              [{art.stock_symbol}]
            </span>
          </div>
          {/* 감성점수 */}
          <div style={{ fontSize: '15px', color: '#0077cc', marginBottom: '8px' }}>
            감성점수: {art.score > 0 ? '+' : ''}{art.score}
          </div>
          {/* 기사 작성 날짜 */}
          <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>{art.date}</div>
          {/* 기사 키워드 */}
          {art.keywords && art.keywords.length > 0 && (
            <div style={{
              margin: '8px 0',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '4px'
            }}>
              {art.keywords.slice(0, 5).map((keyword, idx) => (
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
          )}
          {/* 기사 요약 */}
          {art.summary && (
            <div style={{
              fontSize: '13px',
              color: '#555',
              backgroundColor: '#ffffff',
              padding: '12px',
              borderRadius: '6px',
              border: '1px solid #e0e0e0',
              margin: '8px 0',
              lineHeight: '1.5'
            }}>
              <div style={{ fontWeight: 'bold', fontSize: '12px', color: '#6c757d', marginBottom: '6px' }}>
                📄 기사 요약
              </div>
              {art.summary}
            </div>
          )}
          {/* 기사 본문 확인 버튼 */}
          <button 
            onClick={() => onArticleClick(art)}
            style={{
              backgroundColor: '#0077cc',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer',
              marginTop: '8px'
            }}
          >
            기사 본문 자세히 확인하기
          </button>
        </li>
      ))}
    </ol>
  );
}

export default IndustryArticleList;
