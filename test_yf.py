import yfinance as yf
data = yf.download('^NSEI', start='2024-08-01', end='2024-08-08', interval='1m')
print(data.head())
