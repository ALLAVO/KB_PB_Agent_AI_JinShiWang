import React from 'react';
import './IndustryArticleList.css';

function ArticleDetailModal({ show, article, onClose, closeButtonStyle }) {
  if (!show || !article) return null;

  // 감성점수 색상 결정
  const scoreClass = article.score > 0 ? 'modal-score-positive' : article.score < 0 ? 'modal-score-negative' : 'modal-score-neutral';

  // 기본 닫기 버튼 스타일
  const defaultCloseBtnStyle = {
    marginLeft: '20px',
    marginRight: '10px',
    marginTop: '0',
    fontSize: '28px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: '#888',
    lineHeight: 1
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div style={{display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between'}}>
          <div style={{flex: 1}} />
          <button
            className="modal-close-btn"
            onClick={onClose}
            style={{ ...defaultCloseBtnStyle, ...closeButtonStyle }}
          >
            ×
          </button>
        </div>
        <div className="modal-body">
          <h2 className="modal-title" style={{textAlign: 'left', display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <span>
              {article.article_title}
              <span style={{fontSize: '16px', fontWeight: 400, marginLeft: '10px'}}>
                ({article.date})
              </span>
            </span>
            <span
              className={`modal-score ${scoreClass}`}
              style={{
                marginLeft: '16px',
                fontSize: '16px',
                verticalAlign: 'middle',
                background: 'none',
                color: article.score > 0 ? '#d32f2f' : article.score < 0 ? '#1976d2' : '#888', // 양수: 빨간, 음수: 파란, 0: 회색
                fontWeight: 700,
                textAlign: 'right',
                minWidth: '120px',
                display: 'inline-block'
              }}
            >
              감성점수: {article.score > 0 ? '+' : ''}{article.score}
            </span>
          </h2>
          <div className="modal-meta" style={{display: 'none'}}>
            {/* 기존 날짜, 심볼, 감성점수는 숨김 처리 */}
          </div>
          <div className="modal-article-text" style={{textAlign: 'left'}}>
            {article.article}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ArticleDetailModal;
