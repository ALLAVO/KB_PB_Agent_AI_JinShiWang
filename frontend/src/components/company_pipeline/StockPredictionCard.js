import React from 'react';

function StockPredictionCard({ currentSymbol, getNextWeekInfo, loading, error, prediction }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'flex-start',
      gap: '0px',
      marginTop: '0px',
      marginBottom: '32px',
      minHeight: '180px'
    }}>
      {/* 왼쪽: 이미지 */}
      <div style={{ flex: '0 0 auto', display: 'flex', alignItems: 'flex-start', height: '240px' }}>
        <img
          src={require('../../assets/smile_king.png')}
          alt="smile_king"
          style={{
            height: '240px',
            width: 'auto',
            borderRadius: '0',
            boxShadow: 'none',
            background: 'none',
            // marginLeft: '30px',
            marginRight: '20px'
          }}
        />
      </div>
      {/* 오른쪽: 예측 텍스트 박스 */}
      <div style={{
        background: '#ede8dd',
        borderRadius: '10px',
        padding: '20px 25px',
        minWidth: '450px',
        maxWidth: '900px',
        fontSize: '15px',
        color: '#222',
        lineHeight: '1.2',
        fontWeight: 400,
        boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        border: 'none',
        display: 'flex',
        alignItems: 'left',
        minHeight: '80px',
        textAlign: 'justify'
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
