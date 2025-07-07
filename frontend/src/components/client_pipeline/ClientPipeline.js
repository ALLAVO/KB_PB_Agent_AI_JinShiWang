import React, { useState, useEffect } from 'react';
import { fetchAllClients } from '../../api/clients';
import ClientList from './ClientList';
import ClientDetail from './ClientDetail';
import './ClientPipeline.css';

const ClientPipeline = ({ year, month, weekStr, period, onSetReportTitle, autoCustomerName, autoCustomerTrigger, onAutoCustomerDone }) => {
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [view, setView] = useState('list'); // 'list' | 'detail'

  // 고객 목록 로드
  const loadClients = async () => {
    setLoading(true);
    setError('');
    try {
      const clientsData = await fetchAllClients();
      setClients(clientsData);
    } catch (err) {
      setError('고객 데이터를 불러오는데 실패했습니다: ' + err.message);
      console.error('Client loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClients();
  }, []);

  // 자동 고객 검색 처리
  useEffect(() => {
    if (autoCustomerTrigger && autoCustomerName) {
      const matchedClient = clients.find(client => 
        client.name.toLowerCase().includes(autoCustomerName.toLowerCase())
      );
      if (matchedClient) {
        handleClientSelect(matchedClient);
        if (onAutoCustomerDone) {
          onAutoCustomerDone();
        }
      }
    }
  }, [autoCustomerTrigger, autoCustomerName, clients, onAutoCustomerDone]);

  const handleClientSelect = (client) => {
    setSelectedClient(client);
    setView('detail');
    if (onSetReportTitle) {
      onSetReportTitle(`${client.name}님 리포트`);
    }
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedClient(null);
    if (onSetReportTitle) {
      onSetReportTitle('고객 리포트');
    }
  };

  if (loading) {
    return (
      <div className="client-pipeline-loading">
        <div className="loading-spinner"></div>
        <span>고객 데이터를 불러오는 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="client-pipeline-error">
        <h3>오류가 발생했습니다</h3>
        <p>{error}</p>
        <button className="retry-btn" onClick={loadClients}>
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="client-pipeline-container">
      {view === 'list' ? (
        <ClientList 
          clients={clients}
          onClientSelect={handleClientSelect}
          year={year}
          month={month}
          weekStr={weekStr}
        />
      ) : (
        <ClientDetail
          client={selectedClient}
          onBack={handleBackToList}
          year={year}
          month={month}
          weekStr={weekStr}
          period={period} // period prop 전달
        />
      )}
    </div>
  );
};

export default ClientPipeline;
