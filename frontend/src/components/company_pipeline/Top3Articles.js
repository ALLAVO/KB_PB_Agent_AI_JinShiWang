import React from 'react';

function Top3Articles({ loading, error, top3Articles, findKeywordsForArticle, findSummaryForArticle, handleArticleClick }) {
  return (
    <div className="top3-articles" style={{ width: '900px', maxWidth: '140%'}}>
      {loading ? (
        <div className="stock-chart-loading">핵심 뉴스 데이터를 불러오는 중...</div>
      )
        : error && error !== '종목코드를 입력해주세요'
          ? error
        : top3Articles && top3Articles.top3_articles && top3Articles.top3_articles.length > 0 ? (
          <ol style={{marginTop: '0px', marginLeft: '0px', padding: 0, listStyle: 'none'}}>
            {top3Articles.top3_articles.map((art, idx) => (
              <li key={idx} style={{
                marginBottom: '20px',
                // background: '#f7f6f2',
                // borderRadius: '10px',
                // border: '1.5px solid #e0e0e0',
                // boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                padding: '0px 20px 0px 0px', // 오른쪽 20px, 왼쪽 0px
                position: 'relative',
                minHeight: '120px',
              }}>
                {/* 상단: 제목, 날짜, 감성점수, 키워드 */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: '#ede7db',
                  borderRadius: '10px',
                  padding: '16px 24px 10px 24px',
                  marginBottom: '12px',
                }}>
                  {/* 왼쪽: 기사 제목, 키워드 */}
                  <div style={{flex: 1, minWidth: 0}}>
                    <div style={{
                      fontWeight:'bold',
                      fontSize:'18px',
                      color:'#302A24',
                      marginBottom:'4px',
                      lineHeight:'1.3',
                      textAlign:'left',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}>
                      {art.article_title}
                    </div>
                    <div style={{
                      display:'block',
                      whiteSpace:'nowrap',
                      overflow:'hidden',
                      textOverflow:'clip',
                      marginBottom:'2px',
                      textAlign:'left',
                    }}>
                      {(() => {
                        const articleKeywords = findKeywordsForArticle(art);
                        return articleKeywords && articleKeywords.length > 0 ? (
                          articleKeywords.slice(0, 5).map((keyword, idx) => (
                            <span
                              key={idx}
                              style={{
                                color: '#b48a3c',
                                fontSize: '12px',
                                padding: '2px 5px',
                                borderRadius: '14px',
                                background: 'none',
                                fontWeight: '500',
                                letterSpacing: '0.5px',
                                opacity: 0.7,
                                display: 'inline-block',
                                marginRight: '6px',
                              }}
                            >
                              #{keyword}
                            </span>
                          ))
                        ) : loading ? (
                          <span style={{fontSize: '13px', color: '#bdbdbd', fontStyle: 'italic'}}>키워드 생성 중...</span>
                        ) : null;
                      })()}
                    </div>
                  </div>
                  {/* 오른쪽: 감성점수, 날짜 */}
                  <div style={{display:'flex', flexDirection:'column', alignItems:'flex-end', minWidth:'160px', marginRight:'0px', marginTop:'-5px'}}>
                    <div style={{
                      background:'#fff',
                      color: art.score > 0 ? '#d32f2f' : art.score < 0 ? '#1976d2' : '#302A24', // 양수: 빨간, 음수: 파란, 0: 기본
                      fontWeight:'bold',
                      fontSize:'13px',
                      borderRadius:'10px',
                      padding:'7px 20px',
                      // border:'1.5px solid #e0e0e0',
                      minWidth:'100px',
                      textAlign:'center',
                      marginBottom:'5px',
                    }}>
                      감성점수 : <span style={{fontWeight:'bold', fontSize:'13px'}}>{art.score > 0 ? '+' : ''}{art.score}</span>
                    </div>
                    <div style={{fontSize:'13px', color:'#6d5c3d', fontWeight:'500', background:'#ede7db', borderRadius:'10px', padding:'0px 35px', marginTop:'0'}}>{art.date}</div>
                  </div>
                </div>
                {/* 기사 요약 내용 */}
                {(() => {
                  const summary = findSummaryForArticle(art);
                  return summary ? (
                    <div style={{
                      fontSize: '14px',
                      color: '#302A24',
                      // backgroundColor: '#f8f9fa',
                      padding: '0px 15px 15px 30px',
                      borderRadius: '10px',
                      // border: '1px solid #e9ecef',
                      lineHeight: '1.6',
                      textAlign: 'left',
                      display: 'flex',
                      flexDirection: 'row', // row로 변경
                      alignItems: 'flex-end', // 버튼과 요약을 아래 맞춤
                      gap: '16px' // 요약과 버튼 사이 간격
                    }}>
                      <div style={{width: '100%'}}>
                        {summary.split(/(?=- )/).map((line, idx) => (
                          <React.Fragment key={idx}>
                            {idx !== 0 && <br />}
                            {line.trim()}
                          </React.Fragment>
                        ))}
                      </div>
                      <button 
                        onClick={() => handleArticleClick(art)}
                        style={{
                          backgroundColor: '#F8A70C',
                          color: 'white',
                          border: 'none',
                          padding: '7px 20px', // 좌우 padding을 넓힘
                          borderRadius: '5px',
                          fontSize: '13px',
                          cursor: 'pointer',
                          fontWeight: '700', // medium 대신 700 사용
                          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
                          alignSelf: 'flex-end',
                          marginLeft: '10px',
                          minWidth: '90px', // 버튼 최소 너비 지정
                          whiteSpace: 'nowrap' // 한줄 고정
                        }}
                      >
                        전문보기
                      </button>
                    </div>
                  ) : loading ? (
                    <div style={{
                      fontSize: '12px',
                      color: '#6c757d',
                      fontStyle: 'italic',
                      margin: '12px 0 0 0'
                    }}>
                      요약 생성 중...
                    </div>
                  ) : null;
                })()}
              </li>
            ))}
          </ol>
        ) : '데이터 없음'}
    </div>
  );
}

export default Top3Articles;
