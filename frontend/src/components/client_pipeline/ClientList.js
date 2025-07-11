import React from 'react';
import './ClientPipeline.css';

const ClientList = ({ clients, onClientSelect, year, month, weekStr }) => {
  const formatAmount = (amount) => {
    if (amount >= 100000000) {
      return `${(amount / 100000000).toFixed(1)}억원`;
    } else if (amount >= 10000) {
      return `${(amount / 10000).toFixed(0)}만원`;
    }
    return `${amount.toLocaleString()}원`;
  };

  const getRiskProfileBadge = (riskProfile) => {
    const profiles = {
      'Conservative': { label: '안정형', class: 'conservative' },
      'Moderate': { label: '중립형', class: 'moderate' },
      'Aggressive': { label: '적극형', class: 'aggressive' },
      'Very Conservative': { label: '매우안정형', class: 'very-conservative' },
      'Very Aggressive': { label: '매우적극형', class: 'very-aggressive' }
    };
    
    const profile = profiles[riskProfile] || { label: riskProfile, class: 'default' };
    return (
      <span className={`risk-profile-badge ${profile.class}`}>
        {profile.label}
      </span>
    );
  };

  const getInvestmentHorizonBadge = (horizon) => {
    const horizons = {
      'Short-term': { label: '단기', class: 'short-term' },
      'Medium-term': { label: '중기', class: 'medium-term' },
      'Long-term': { label: '장기', class: 'long-term' }
    };
    
    const horizonInfo = horizons[horizon] || { label: horizon, class: 'default' };
    return (
      <span className={`investment-horizon-badge ${horizonInfo.class}`}>
        {horizonInfo.label}
      </span>
    );
  };

  return (
    <div>
      <div className="client-list-header" style={{ marginBottom: '16px' }}>
        <h2 className="client-list-title">
          <span className="title-icon">👥</span>
          고객 관리
        </h2>
        <div className="client-list-summary">
          <span className="period-info">{year}년 {month}월 {weekStr}</span>
          <span className="total-clients">총 {clients.length}명의 고객</span>
        </div>
      </div>

      {clients.length === 0 ? (
        <div className="no-clients-message">
          <div className="no-clients-icon">👥</div>
          <h3>등록된 고객이 없습니다</h3>
          <p>새로운 고객을 등록해주세요.</p>
        </div>
      ) : (
        <table style={{
          width: '100%',
          borderCollapse: 'separate',
          borderSpacing: 0,
          background: 'white',
          borderRadius: '10px',
          overflow: 'hidden',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
        }}>
          <thead style={{ background: 'rgba(234,227,215,0.7)', borderRadius: '6px 6px 0 0' }}>
            <tr style={{ background: 'rgba(234,227,215,0.7)', height: 60 }}>
              <th style={{
                padding: '24px 16px',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem',
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 100,
                borderTopLeftRadius: '6px',
                borderBottom: '1.5px solid #e5dfd3',
              }}>고객명</th>
              <th style={{
                padding: '24px 16px',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem',
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 80,
                borderBottom: '1.5px solid #e5dfd3',
              }}>성별</th>
              <th style={{
                padding: '24px 16px',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem',
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 80,
                borderBottom: '1.5px solid #e5dfd3',
              }}>나이</th>
              <th style={{
                padding: '24px 16px',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem',
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 120,
                borderBottom: '1.5px solid #e5dfd3',
              }}>위험성향</th>
              <th style={{
                padding: '24px 16px',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem',
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 100,
                borderBottom: '1.5px solid #e5dfd3',
              }}>투자기간</th>
              <th style={{
                padding: '24px 16px',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem',
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 120,
                borderTopRightRadius: '6px',
                borderBottom: '1.5px solid #e5dfd3',
              }}>투자금액</th>
            </tr>
          </thead>
          <tbody style={{ background: '#fff', borderRadius: '0 0 6px 6px' }}>
            {clients.map((client, idx) => (
              <tr key={client.id} style={{
                background: '#fff',
                borderBottom: idx < clients.length - 1 ? '1.5px solid #ede9e2' : 'none',
                height: 56
              }}>
                <td style={{
                  padding: '12px 16px',
                  textAlign: 'center',
                  fontWeight: 500,
                  fontSize: '1.1rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                  borderBottomLeftRadius: idx === clients.length - 1 ? '6px' : 0,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    {client.name}
                    <button 
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                      onClick={() => onClientSelect(client)}
                      title="상세 분석 보기"
                    >
                      <img 
                        src={require('../../assets/magnifier.png')}
                        alt="상세 분석"
                        style={{
                          width: '16px',
                          height: '16px',
                          opacity: 0.7,
                        }}
                        onMouseOver={(e) => {
                          e.target.style.opacity = 1;
                        }}
                        onMouseOut={(e) => {
                          e.target.style.opacity = 0.7;
                        }}
                      />
                    </button>
                  </div>
                </td>
                <td style={{
                  padding: '12px 16px',
                  textAlign: 'center',
                  fontWeight: 400,
                  fontSize: '1.0rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                }}>{client.sex}</td>
                <td style={{
                  padding: '12px 16px',
                  textAlign: 'center',
                  fontWeight: 400,
                  fontSize: '1.0rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                }}>{client.age}세</td>
                <td style={{
                  padding: '12px 16px',
                  textAlign: 'center',
                  fontWeight: 400,
                  fontSize: '1.0rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                }}>
                  {getRiskProfileBadge(client.risk_profile)}
                </td>
                <td style={{
                  padding: '12px 16px',
                  textAlign: 'center',
                  fontWeight: 400,
                  fontSize: '1.0rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                }}>
                  {getInvestmentHorizonBadge(client.investment_horizon)}
                </td>
                <td style={{
                  padding: '12px 16px',
                  textAlign: 'center',
                  fontWeight: 500,
                  fontSize: '1.0rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                  borderBottomRightRadius: idx === clients.length - 1 ? '6px' : 0,
                }}>{formatAmount(client.total_amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ClientList;
