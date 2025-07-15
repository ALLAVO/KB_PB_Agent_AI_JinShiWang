import React from "react";
import "./IndustryCompanyTable.css";

function IndustryCompanyTable({ companiesData, loadingCompanies, formatNumber, formatPercentage }) {
  if (loadingCompanies) {
    return <div className="industry-companies-loading">기업 정보를 불러오는 중...</div>;
  }
  if (!companiesData || !companiesData.companies || companiesData.companies.length === 0) {
    return <div className="industry-companies-nodata">해당 산업의 기업 데이터가 없습니다.</div>;
  }
  return (
    <div className="industry-company-table-wrapper">
      <table className="industry-company-table">
        <thead>
          <tr>
            <th rowSpan="2">티커</th>
            <th rowSpan="2">현재가($)</th>
            <th rowSpan="2">시가총액(M$)</th>
            <th colSpan="3">수익률</th>
            <th colSpan="3">Valuation 지표</th>
          </tr>
          <tr>
            <th>1W</th>
            <th>1M</th>
            <th>1Y</th>
            <th>P/E(배)</th>
            <th>P/B(배)</th>
            <th>ROE(%)</th>
          </tr>
        </thead>
        <tbody>
          {companiesData.companies.map((company, index) => (
            <tr key={company.ticker}>
              <td>{company.ticker}</td>
              <td>${company.current_price || 'N/A'}</td>
              <td>{formatNumber(company.market_cap_millions)}</td>
              <td className={company.return_1week >= 0 ? "positive" : "negative"}>{formatPercentage(company.return_1week)}</td>
              <td className={company.return_1month >= 0 ? "positive" : "negative"}>{formatPercentage(company.return_1month)}</td>
              <td className={company.return_1year >= 0 ? "positive" : "negative"}>{formatPercentage(company.return_1year)}</td>
              <td>{company.pe_ratio || 'N/A'}</td>
              <td>{company.pb_ratio || 'N/A'}</td>
              <td>{company.roe ? `${company.roe}%` : 'N/A'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default IndustryCompanyTable;
