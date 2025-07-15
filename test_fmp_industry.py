#!/usr/bin/env python3

from app.services.industry_analysis import get_industry_top10_companies
import json

def test_industry_analysis():
    print("🚀 Testing FMP-based industry analysis...")
    
    # Test Technology sector
    result = get_industry_top10_companies('Technology', '2024-01-19')
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    companies = result.get('companies', [])
    print(f"✅ Technology sector analysis returned {len(companies)} companies")
    
    if companies:
        print("\n📊 Top 5 companies:")
        for i, company in enumerate(companies[:5]):
            ticker = company.get('ticker')
            market_cap = company.get('market_cap_millions')
            pe_ratio = company.get('pe_ratio')
            pb_ratio = company.get('pb_ratio')
            roe = company.get('roe')
            
            print(f"  {i+1}. {ticker}")
            print(f"     Market Cap: ${market_cap}M")
            print(f"     P/E: {pe_ratio}, P/B: {pb_ratio}, ROE: {roe}%")
            print()

if __name__ == "__main__":
    test_industry_analysis()
