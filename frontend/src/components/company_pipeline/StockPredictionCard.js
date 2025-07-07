import React from 'react';

function StockPredictionCard({ currentSymbol, getNextWeekInfo, loading, error, prediction }) {
  return (
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
  );
}

export default StockPredictionCard;
