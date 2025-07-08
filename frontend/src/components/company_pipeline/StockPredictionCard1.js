import React from 'react';

function StockPredictionCard({ currentSymbol, getNextWeekInfo, loading, error, prediction }) {
  return (
    <div style={{
      width: '100%',
      marginTop: '0px',
      marginBottom: '32px',
      minHeight: '80px',
      display: 'flex',
      justifyContent: 'center',
    }}>
      {/* 오른쪽: 예측 텍스트 박스만 전체를 차지 */}
      <div style={{
        background: '#ede8dd',
        borderRadius: '10px',
        padding: '28px 40px',
        width: '100%',
        maxWidth: '900px',
        fontSize: '15px',
        color: '#222',
        lineHeight: '1.2',
        fontWeight: 400,
        boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        border: 'none',
        minHeight: '30px',
        textAlign: 'justify',
        display: 'flex',
        alignItems: 'center',
      }}>
        {loading ? null : error && error !== '종목코드를 입력해주세요' ? (
          <span style={{ color: '#d32f2f', fontStyle: 'italic', fontSize: '18px' }}>
            주가 전망 데이터를 불러오지 못했습니다.
          </span>
        ) : prediction && prediction.summary ? (
          prediction.summary
        ) : (
          <span style={{ color: '#666', fontStyle: 'italic', fontSize: '18px' }}>
            주가 전망 데이터가 없습니다.
          </span>
        )}
      </div>
    </div>
  );
}

export default StockPredictionCard;
