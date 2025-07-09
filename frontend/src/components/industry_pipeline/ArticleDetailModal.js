import React from "react";

function ArticleDetailModal({ article, onClose }) {
  if (!article) return null;
  return (
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
          onClick={onClose}
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
            {article.article_title}
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
              {article.date}
            </span>
            <span style={{
              fontSize: '14px',
              color: '#666',
              backgroundColor: '#e3f2fd',
              padding: '4px 8px',
              borderRadius: '4px'
            }}>
              {article.stock_symbol}
            </span>
            <span style={{
              fontSize: '16px',
              fontWeight: 'bold',
              color: article.score > 0 ? '#22c55e' : article.score < 0 ? '#ef4444' : '#666',
              backgroundColor: '#f9f9f9',
              padding: '4px 8px',
              borderRadius: '4px'
            }}>
              감성점수: {article.score > 0 ? '+' : ''}{article.score}
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
            {article.article}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ArticleDetailModal;
