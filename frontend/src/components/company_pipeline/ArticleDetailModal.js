import React from 'react';
import './Top3Articles.css';

function ArticleDetailModal({ show, article, onClose }) {
  if (!show || !article) return null;

  // 감성점수 색상 결정
  const scoreClass = article.score > 0 ? 'modal-score-positive' : article.score < 0 ? 'modal-score-negative' : 'modal-score-neutral';

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <button className="modal-close-btn" onClick={onClose}>
          ×
        </button>
        <div className="modal-body">
          <h2 className="modal-title">{article.article_title}</h2>
          <div className="modal-meta">
            <span className="modal-date">{article.date}</span>
            <span className="modal-symbol">{article.stock_symbol}</span>
            <span className={`modal-score ${scoreClass}`}>
              감성점수: {article.score > 0 ? '+' : ''}{article.score}
            </span>
          </div>
          <div className="modal-article-text">
            {article.article}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ArticleDetailModal;
