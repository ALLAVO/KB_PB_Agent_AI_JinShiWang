import React from "react";

/**
 * 미국 주요 지수 1년치 데이터를 테이블 형식으로 보여주는 컴포넌트
 * @param {Object} props
 * @param {Object} props.indices1YearData - 1년치 지수 데이터 (dow, sp500, nasdaq)
 * @param {boolean} props.loading - 로딩 상태
 * @param {string} props.error - 에러 메시지
 */
function MarketIndices1YearTable({ indices1YearData, loading, error }) {
  // 1년치 데이터를 테이블 형식으로 변환
  const generateTableDataFrom1Year = () => {
    if (!indices1YearData || indices1YearData.error) {
      return [
        { 지수: 'DOW', '금요일종가(pt)': '-', '등락률(%)': { '1W': '-', '1M': '-', 'YTD': '-' }, '변동성(%)': { '1M': '-' } },
        { 지수: 'S&P 500', '금요일종가(pt)': '-', '등락률(%)': { '1W': '-', '1M': '-', 'YTD': '-' }, '변동성(%)': { '1M': '-' } },
        { 지수: 'NASDAQ', '금요일종가(pt)': '-', '등락률(%)': { '1W': '-', '1M': '-', 'YTD': '-' }, '변동성(%)': { '1M': '-' } }
      ];
    }

    const calculatePeriodReturn = (closes, days) => {
      if (!closes || closes.length < days) return 0;
      const current = closes[closes.length - 1];
      const past = closes[closes.length - 1 - days];
      return past ? (((current - past) / past) * 100).toFixed(1) : 0;
    };

    const calculateVolatility = (closes, days) => {
      if (!closes || closes.length < days) return 0;
      const recentCloses = closes.slice(-days);
      const returns = [];
      for (let i = 1; i < recentCloses.length; i++) {
        const dailyReturn = (recentCloses[i] - recentCloses[i-1]) / recentCloses[i-1];
        returns.push(dailyReturn);
      }
      if (returns.length === 0) return 0;
      const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length;
      const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
      return (Math.sqrt(variance) * Math.sqrt(252) * 100).toFixed(1); // 연율화
    };

    const result = [];
    
    // DOW
    if (indices1YearData.dow && indices1YearData.dow.closes && indices1YearData.dow.closes.length > 0) {
      const dowCloses = indices1YearData.dow.closes;
      const currentPrice = dowCloses[dowCloses.length - 1];
      result.push({
        지수: 'DOW',
        '금요일종가(pt)': currentPrice ? currentPrice.toLocaleString() : '-',
        '등락률(%)': {
          '1W': calculatePeriodReturn(dowCloses, 7),
          '1M': calculatePeriodReturn(dowCloses, 30),
          'YTD': calculatePeriodReturn(dowCloses, dowCloses.length - 1)
        },
        '변동성(%)': {
          '1M': calculateVolatility(dowCloses, 30)
        }
      });
    }

    // S&P500
    if (indices1YearData.sp500 && indices1YearData.sp500.closes && indices1YearData.sp500.closes.length > 0) {
      const sp500Closes = indices1YearData.sp500.closes;
      const currentPrice = sp500Closes[sp500Closes.length - 1];
      result.push({
        지수: 'S&P 500',
        '금요일종가(pt)': currentPrice ? currentPrice.toLocaleString() : '-',
        '등락률(%)': {
          '1W': calculatePeriodReturn(sp500Closes, 7),
          '1M': calculatePeriodReturn(sp500Closes, 30),
          'YTD': calculatePeriodReturn(sp500Closes, sp500Closes.length - 1)
        },
        '변동성(%)': {
          '1M': calculateVolatility(sp500Closes, 30)
        }
      });
    }

    // NASDAQ
    if (indices1YearData.nasdaq && indices1YearData.nasdaq.closes && indices1YearData.nasdaq.closes.length > 0) {
      const nasdaqCloses = indices1YearData.nasdaq.closes;
      const currentPrice = nasdaqCloses[nasdaqCloses.length - 1];
      result.push({
        지수: 'NASDAQ',
        '금요일종가(pt)': currentPrice ? currentPrice.toLocaleString() : '-',
        '등락률(%)': {
          '1W': calculatePeriodReturn(nasdaqCloses, 7),
          '1M': calculatePeriodReturn(nasdaqCloses, 30),
          'YTD': calculatePeriodReturn(nasdaqCloses, nasdaqCloses.length - 1)
        },
        '변동성(%)': {
          '1M': calculateVolatility(nasdaqCloses, 30)
        }
      });
    }

    return result.length > 0 ? result : [
      { 지수: 'DOW', '금요일종가(pt)': '-', '등락률(%)': { '1W': '-', '1M': '-', 'YTD': '-' }, '변동성(%)': { '1M': '-' } },
      { 지수: 'S&P 500', '금요일종가(pt)': '-', '등락률(%)': { '1W': '-', '1M': '-', 'YTD': '-' }, '변동성(%)': { '1M': '-' } },
      { 지수: 'NASDAQ', '금요일종가(pt)': '-', '등락률(%)': { '1W': '-', '1M': '-', 'YTD': '-' }, '변동성(%)': { '1M': '-' } }
    ];
  };

  const tableData = generateTableDataFrom1Year();

  return (
    <div style={{ marginTop: '0px', marginBottom: '16px' }}>
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          1년치 데이터를 불러오는 중...
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
          borderRadius: '10px', // 더 확실하게 적용
          overflow: 'hidden',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
        }}>
          <thead style={{background: 'rgba(234,227,215,0.7)', borderRadius: '6px 6px 0 0'}}>
            <tr style={{ background: 'rgba(234,227,215,0.7)', height: 60 }}>
              <th style={{
                padding: '24px 0 24px 0',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem', // 1.3 -> 1.2
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 80,
                borderTopLeftRadius: '6px',
                borderBottom: '1.5px solid #e5dfd3',
              }} rowSpan="2">지수</th>
              <th style={{
                padding: '24px 0 24px 0',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem', // 1.3 -> 1.2
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 100,
                borderBottom: '1.5px solid #e5dfd3',
              }} rowSpan="2">금요일 종가<br/>(pt)</th>
              <th style={{
                padding: '10px 0 10px 0',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem', // 1.3 -> 1.2
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 180,
                borderBottom: 'none',
              }} colSpan="3">등락률(%)</th>
              <th style={{
                padding: '24px 0 24px 0',
                textAlign: 'center',
                fontWeight: 500,
                fontSize: '1.2rem', // 1.3 -> 1.2
                color: '#363532',
                border: 'none',
                letterSpacing: '-1px',
                minWidth: 80,
                borderTopRightRadius: '6px',
                borderBottom: '1.5px solid #e5dfd3',
              }} rowSpan="2">변동성(%)<br/>1M</th>
            </tr>
            <tr style={{ background: 'rgba(234,227,215,0.7)', height: 32 }}>
              <th style={{
                padding: '0 0 10px 0',
                textAlign: 'center',
                fontWeight: 400,
                fontSize: '1.0rem', // 1.1 -> 1.0
                color: '#363532',
                border: 'none',
                background: 'none',
                borderBottom: '1.5px solid #e5dfd3',
              }}>1W</th>
              <th style={{
                padding: '0 0 10px 0',
                textAlign: 'center',
                fontWeight: 400,
                fontSize: '1.0rem', // 1.1 -> 1.0
                color: '#363532',
                border: 'none',
                background: 'none',
                borderBottom: '1.5px solid #e5dfd3',
              }}>1M</th>
              <th style={{
                padding: '0 0 10px 0',
                textAlign: 'center',
                fontWeight: 400,
                fontSize: '1.0rem', // 1.1 -> 1.0
                color: '#363532',
                border: 'none',
                background: 'none',
                borderBottom: '1.5px solid #e5dfd3',
              }}>YTD</th>
            </tr>
          </thead>
          <tbody style={{background: '#fff', borderRadius: '0 0 6px 6px'}}>
            {tableData.map((row, idx) => (
              <tr key={idx} style={{
                background: '#fff',
                borderBottom: idx < tableData.length - 1 ? '1.5px solid #ede9e2' : 'none',
                height: 44
              }}>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500, // 기존 700에서 500으로 변경
                  fontSize: '1.2rem', // 1.3 -> 1.2
                  color: '#363532',
                  letterSpacing: '-1px',
                  borderBottomLeftRadius: idx === tableData.length - 1 ? '6px' : 0,
                }}>{row.지수}</td>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 400,
                  fontSize: '1.2rem', // 1.3 -> 1.2
                  color: '#363532',
                  letterSpacing: '-1px',
                }}>{row['금요일종가(pt)']}</td>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500, // medium
                  fontSize: '1.2rem', // 1.3 -> 1.2
                  color: row['등락률(%)']['1W'] > 0 ? '#ef4444' : row['등락률(%)']['1W'] < 0 ? '#2563eb' : '#363532', // 빨강/파랑/기본
                  letterSpacing: '-1px',
                }}>{row['등락률(%)']['1W'] !== '-' ? (row['등락률(%)']['1W'] > 0 ? '+' : '') + row['등락률(%)']['1W'] : '-'}</td>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500, // medium
                  fontSize: '1.2rem', // 1.3 -> 1.2
                  color: row['등락률(%)']['1M'] > 0 ? '#ef4444' : row['등락률(%)']['1M'] < 0 ? '#2563eb' : '#363532',
                  letterSpacing: '-1px',
                }}>{row['등락률(%)']['1M'] !== '-' ? (row['등락률(%)']['1M'] > 0 ? '+' : '') + row['등락률(%)']['1M'] : '-'}</td>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 500, // medium
                  fontSize: '1.2rem', // 1.3 -> 1.2
                  color: row['등락률(%)']['YTD'] > 0 ? '#ef4444' : row['등락률(%)']['YTD'] < 0 ? '#2563eb' : '#363532',
                  letterSpacing: '-1px',
                }}>{row['등락률(%)']['YTD'] !== '-' ? (row['등락률(%)']['YTD'] > 0 ? '+' : '') + row['등락률(%)']['YTD'] : '-'}</td>
                <td style={{
                  padding: '6px 0',
                  textAlign: 'center',
                  fontWeight: 400,
                  fontSize: '1.2rem', // 1.3 -> 1.2
                  color: '#363532',
                  letterSpacing: '-1px',
                  borderBottomRightRadius: idx === tableData.length - 1 ? '6px' : 0,
                }}>{row['변동성(%)']['1M']}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default MarketIndices1YearTable;
