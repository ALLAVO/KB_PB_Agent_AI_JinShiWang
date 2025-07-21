import React from "react";

/**
 * FICC 1년치 데이터를 테이블 형식으로 보여주는 컴포넌트
 * @param {Object} props
 * @param {Object} props.treasuryData1Year - 1년치 미국 국채 금리 데이터
 * @param {Object} props.fxData1Year - 1년치 환율 데이터
 * @param {boolean} props.loading - 로딩 상태
 * @param {string} props.error - 에러 메시지
 */
function FiccTable1Year({ treasuryData1Year, fxData1Year, loading, error }) {
  // 1년치 데이터를 테이블 형식으로 변환
  const generateFiccTableData = () => {
    const tableData = [];

    // 미국 국채 데이터 처리
    if (treasuryData1Year && !treasuryData1Year.error && treasuryData1Year.us_2y && treasuryData1Year.us_10y) {
      const us2yRates = treasuryData1Year.us_2y;
      const us10yRates = treasuryData1Year.us_10y;

      if (us2yRates.length > 0) {
        const current2y = us2yRates[us2yRates.length - 1];
        const change1W_2y = us2yRates.length >= 7 ? current2y - us2yRates[us2yRates.length - 8] : 0;
        const change1M_2y = us2yRates.length >= 30 ? current2y - us2yRates[us2yRates.length - 31] : 0;
        const changeYTD_2y = us2yRates.length > 1 ? current2y - us2yRates[0] : 0;

        tableData.push({
          구분: 'US 2Y',
          '금요일 기준 종가': current2y ? current2y.toFixed(2) + '%' : '-',
          '등락률': {
            '1W': change1W_2y !== 0 ? (change1W_2y > 0 ? '+' : '') + change1W_2y.toFixed(2) + 'bp' : '-',
            '1M': change1M_2y !== 0 ? (change1M_2y > 0 ? '+' : '') + (change1M_2y * 100).toFixed(0) + 'bp' : '-',
            'YTD': changeYTD_2y !== 0 ? (changeYTD_2y > 0 ? '+' : '') + (changeYTD_2y * 100).toFixed(0) + 'bp' : '-'
          },
          change1W_2y,
          change1M_2y,
          changeYTD_2y
        });
      }

      if (us10yRates.length > 0) {
        const current10y = us10yRates[us10yRates.length - 1];
        const change1W_10y = us10yRates.length >= 7 ? current10y - us10yRates[us10yRates.length - 8] : 0;
        const change1M_10y = us10yRates.length >= 30 ? current10y - us10yRates[us10yRates.length - 31] : 0;
        const changeYTD_10y = us10yRates.length > 1 ? current10y - us10yRates[0] : 0;

        tableData.push({
          구분: 'US 10Y',
          '금요일 기준 종가': current10y ? current10y.toFixed(2) + '%' : '-',
          '등락률': {
            '1W': change1W_10y !== 0 ? (change1W_10y > 0 ? '+' : '') + change1W_10y.toFixed(2) + 'bp' : '-',
            '1M': change1M_10y !== 0 ? (change1M_10y > 0 ? '+' : '') + (change1M_10y * 100).toFixed(0) + 'bp' : '-',
            'YTD': changeYTD_10y !== 0 ? (changeYTD_10y > 0 ? '+' : '') + (changeYTD_10y * 100).toFixed(0) + 'bp' : '-'
          },
          change1W_10y,
          change1M_10y,
          changeYTD_10y
        });
      }
    } else {
      // 에러 또는 데이터 없을 때 기본값
      tableData.push(
        {
          구분: 'US 2Y',
          '금요일 기준 종가': '-',
          '등락률': { '1W': '-', '1M': '-', 'YTD': '-' },
          change1W_2y: 0,
          change1M_2y: 0,
          changeYTD_2y: 0
        },
        {
          구분: 'US 10Y',
          '금요일 기준 종가': '-',
          '등락률': { '1W': '-', '1M': '-', 'YTD': '-' },
          change1W_10y: 0,
          change1M_10y: 0,
          changeYTD_10y: 0
        }
      );
    }

    // 환율 데이터 처리
    if (fxData1Year && !fxData1Year.error && fxData1Year.usd_krw && fxData1Year.eur_usd) {
      const usdKrwRates = fxData1Year.usd_krw.filter(rate => rate !== null && rate !== undefined);
      const eurUsdRates = fxData1Year.eur_usd.filter(rate => rate !== null && rate !== undefined);

      if (usdKrwRates.length > 0) {
        const currentUsdKrw = usdKrwRates[usdKrwRates.length - 1];
        const change1W_usd = usdKrwRates.length >= 7 ? currentUsdKrw - usdKrwRates[usdKrwRates.length - 8] : 0;
        const change1M_usd = usdKrwRates.length >= 30 ? currentUsdKrw - usdKrwRates[usdKrwRates.length - 31] : 0;
        const changeYTD_usd = usdKrwRates.length > 1 ? currentUsdKrw - usdKrwRates[0] : 0;

        tableData.push({
          구분: 'USD/KRW',
          '금요일 기준 종가': currentUsdKrw ? currentUsdKrw.toLocaleString() + ' KRW' : '-',
          '등락률': {
            '1W': change1W_usd !== 0 ? (change1W_usd > 0 ? '+' : '') + change1W_usd.toFixed(0) + ' KRW' : '-',
            '1M': change1M_usd !== 0 ? (change1M_usd > 0 ? '+' : '') + change1M_usd.toFixed(0) + ' KRW' : '-',
            'YTD': changeYTD_usd !== 0 ? (changeYTD_usd > 0 ? '+' : '') + changeYTD_usd.toFixed(0) + ' KRW' : '-'
          },
          change1W_usd,
          change1M_usd,
          changeYTD_usd
        });
      }

      if (eurUsdRates.length > 0) {
        const currentEurUsd = eurUsdRates[eurUsdRates.length - 1];
        const change1W_eur = eurUsdRates.length >= 7 ? currentEurUsd - eurUsdRates[eurUsdRates.length - 8] : 0;
        const change1M_eur = eurUsdRates.length >= 30 ? currentEurUsd - eurUsdRates[eurUsdRates.length - 31] : 0;
        const changeYTD_eur = eurUsdRates.length > 1 ? currentEurUsd - eurUsdRates[0] : 0;

        tableData.push({
          구분: 'EUR/USD',
          '금요일 기준 종가': currentEurUsd ? currentEurUsd.toFixed(4) + ' USD' : '-',
          '등락률': {
            '1W': change1W_eur !== 0 ? (change1W_eur > 0 ? '+' : '') + change1W_eur.toFixed(4) + ' USD' : '-',
            '1M': change1M_eur !== 0 ? (change1M_eur > 0 ? '+' : '') + change1M_eur.toFixed(4) + ' USD' : '-',
            'YTD': changeYTD_eur !== 0 ? (changeYTD_eur > 0 ? '+' : '') + changeYTD_eur.toFixed(4) + ' USD' : '-'
          },
          change1W_eur,
          change1M_eur,
          changeYTD_eur
        });
      }
    } else {
      // 에러 또는 데이터 없을 때 기본값
      tableData.push(
        {
          구분: 'USD/KRW',
          '금요일 기준 종가': '-',
          '등락률': { '1W': '-', '1M': '-', 'YTD': '-' },
          change1W_usd: 0,
          change1M_usd: 0,
          changeYTD_usd: 0
        },
        {
          구분: 'EUR/USD',
          '금요일 기준 종가': '-',
          '등락률': { '1W': '-', '1M': '-', 'YTD': '-' },
          change1W_eur: 0,
          change1M_eur: 0,
          changeYTD_eur: 0
        }
      );
    }

    return tableData;
  };

  const tableData = generateFiccTableData();

  const getColorByChange = (value) => {
    if (value > 0) return '#ef4444'; // 빨간색 (상승)
    if (value < 0) return '#2563eb'; // 파란색 (하락)
    return '#363532'; // 기본색 (변화없음)
  };

  return (
    <div style={{ marginTop: '16px', marginBottom: '16px' }}>
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          FICC 1년치 데이터를 불러오는 중...
        </div>
      ) : error ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#d32f2f' }}>
          {error}
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
                padding: '24px 0 24px 0',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem',
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 80,
                borderTopLeftRadius: '6px',
                borderBottom: '1.5px solid #e5dfd3',
              }} rowSpan="2">구분</th>
              <th style={{
                padding: '24px 0 24px 0',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem',
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 100,
                borderBottom: '1.5px solid #e5dfd3',
              }} rowSpan="2">금요일 기준 종가</th>
              <th style={{
                padding: '10px 0 10px 0',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem',
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 180,
                borderBottom: 'none',
                borderTopRightRadius: '6px',
              }} colSpan="3">등락률(%)</th>
            </tr>
            <tr style={{ background: 'rgba(234,227,215,0.7)', height: 32 }}>
              <th style={{
                padding: '0 0 10px 0',
                textAlign: 'center',
                fontWeight: 400,
                fontSize: '1.0rem',
                color: '#363532',
                border: 'none',
                background: 'none',
                borderBottom: '1.5px solid #e5dfd3',
              }}>1W</th>
              <th style={{
                padding: '0 0 10px 0',
                textAlign: 'center',
                fontWeight: 400,
                fontSize: '1.0rem',
                color: '#363532',
                border: 'none',
                background: 'none',
                borderBottom: '1.5px solid #e5dfd3',
              }}>1M</th>
              <th style={{
                padding: '0 0 10px 0',
                textAlign: 'center',
                fontWeight: 400,
                fontSize: '1.0rem',
                color: '#363532',
                border: 'none',
                background: 'none',
                borderBottom: '1.5px solid #e5dfd3',
              }}>YTD</th>
            </tr>
          </thead>
          <tbody style={{ background: '#fff', borderRadius: '0 0 6px 6px' }}>
            {tableData.map((row, idx) => (
              <tr key={idx} style={{
                background: '#fff',
                borderBottom: idx < tableData.length - 1 ? '1.5px solid #ede9e2' : 'none',
                height: 44
              }}>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500,
                  fontSize: '1.2rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                  borderBottomLeftRadius: idx === tableData.length - 1 ? '6px' : 0,
                }}>{row.구분}</td>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 400,
                  fontSize: '1.2rem',
                  color: '#363532',
                  letterSpacing: '-1px',
                }}>{row['금요일 기준 종가']}</td>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500,
                  fontSize: '1.2rem',
                  color: getColorByChange(
                    row.구분 === 'US 2Y' ? row.change1W_2y :
                    row.구분 === 'US 10Y' ? row.change1W_10y :
                    row.구분 === 'USD/KRW' ? row.change1W_usd :
                    row.change1W_eur
                  ),
                  letterSpacing: '-1px',
                }}>{row['등락률']['1W']}</td>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500,
                  fontSize: '1.2rem',
                  color: getColorByChange(
                    row.구분 === 'US 2Y' ? row.change1M_2y :
                    row.구분 === 'US 10Y' ? row.change1M_10y :
                    row.구분 === 'USD/KRW' ? row.change1M_usd :
                    row.change1M_eur
                  ),
                  letterSpacing: '-1px',
                }}>{row['등락률']['1M']}</td>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500,
                  fontSize: '1.2rem',
                  color: getColorByChange(
                    row.구분 === 'US 2Y' ? row.changeYTD_2y :
                    row.구분 === 'US 10Y' ? row.changeYTD_10y :
                    row.구분 === 'USD/KRW' ? row.changeYTD_usd :
                    row.changeYTD_eur
                  ),
                  letterSpacing: '-1px',
                  borderBottomRightRadius: idx === tableData.length - 1 ? '6px' : 0,
                }}>{row['등락률']['YTD']}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default FiccTable1Year;
