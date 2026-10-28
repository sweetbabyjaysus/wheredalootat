"""Check every data host is reachable before a run."""
import requests

HOSTS = {
    "Yahoo Finance (yfinance)": "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d",
    "Yahoo Finance (fc)": "https://fc.yahoo.com",
    "SEC EDGAR": "https://www.sec.gov/files/company_tickers.json",
    "SEC data API": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
    "FRED": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",
    "Japan MoF": "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv",
    "Federal Reserve": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
    "Bank of Japan": "https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm",
    "BLS (CPI calendar)": "https://www.bls.gov/schedule/news_release/cpi.htm",
    "Google News RSS": "https://news.google.com/rss/search?q=ASML",
}

if __name__ == "__main__":
    bad = 0
    for name, url in HOSTS.items():
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "connectivity-check research@example.com"})
            status = str(r.status_code)
        except Exception as e:
            status, bad = f"FAIL ({type(e).__name__}: {str(e)[:80]})", bad + 1
        print(f"{name:28s} {status}")
    raise SystemExit(1 if bad else 0)
