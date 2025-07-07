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

  const getClientImage = (clientName) => {
    try {
      return require(`../../assets/client_profile/${clientName}.png`);
    } catch (error) {
      return require('../../assets/client_profile/default.png');
    }
  };

  return (
    <div className="client-list-container">
      <div className="client-list-header">
        <h2 className="client-list-title">
          <span className="title-icon">👥</span>
          고객 관리
        </h2>
        <div className="client-list-summary">
          <span className="period-info">{year}년 {month}월 {weekStr}</span>
          <span className="total-clients">총 {clients.length}명의 고객</span>
        </div>
      </div>

      <div className="client-grid">
        {clients.map((client) => (
          <div key={client.id} className="client-card">
            <div className="client-card-header">
              <div className="client-avatar">
                <img 
                  src={getClientImage(client.name)}
                  alt={client.name}
                  onError={(e) => {
                    try {
                      e.target.src = require('../../assets/client_profile/default.png');
                    } catch (error) {
                      // fallback: 기본 아바타 또는 빈 이미지
                      e.target.style.display = 'none';
                    }
                  }}
                />
              </div>
              <div className="client-basic-info">
                <h3 className="client-name">{client.name}</h3>
                <div className="client-demographics">
                  <span className="client-sex">{client.sex}</span>
                  <span className="client-age">{client.age}세</span>
                </div>
              </div>
            </div>

            <div className="client-card-body">
              <div className="client-investment-info">
                <div className="investment-item">
                  <span className="investment-label">위험성향:</span>
                  {getRiskProfileBadge(client.risk_profile)}
                </div>
                <div className="investment-item">
                  <span className="investment-label">투자기간:</span>
                  {getInvestmentHorizonBadge(client.investment_horizon)}
                </div>
                <div className="investment-item total-amount">
                  <span className="investment-label">총 투자금액:</span>
                  <span className="amount-value">{formatAmount(client.total_amount)}</span>
                </div>
              </div>
            </div>

            <div className="client-card-footer">
              <button 
                className="client-detail-btn"
                onClick={() => onClientSelect(client)}
              >
                <span className="btn-icon"></span>
                상세 분석 보기
              </button>
            </div>
          </div>
        ))}
      </div>

      {clients.length === 0 && (
        <div className="no-clients-message">
          <div className="no-clients-icon">👥</div>
          <h3>등록된 고객이 없습니다</h3>
          <p>새로운 고객을 등록해주세요.</p>
        </div>
      )}
    </div>
  );
};

export default ClientList;
