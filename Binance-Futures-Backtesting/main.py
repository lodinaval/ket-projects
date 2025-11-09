import pandas as pd
from time import sleep
import ta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG
from helper import get_tickers_usdt, klines, klines_extended

# Take Profit and Stop Loss. 0.03 means 3%
tp = 0.03   
sl = 0.02
# Timeframe (for example, '1m', '3m', '5m', '15m', '1h', '4h')
timeframe = '5m'
# Interval in days:
interval = 60


# symbols = get_tickers_usdt()

# RSI indicator function. Returns dataframe
def rsi(df, period=14):
    rsi = ta.momentum.RSIIndicator(pd.Series(df), window=period).rsi()
    return rsi

def ema(df, period=200):
    ema = ta.trend.EMAIndicator(pd.Series(df), period).ema_indicator()
    return ema

def macd(df):
    macd = ta.trend.MACD(pd.Series(df)).macd()
    return macd

def bol_h(df, period = 20, dev=2):
    return ta.volatility.BollingerBands(pd.Series(df)).bollinger_hband()
def bol_l(df, period = 20, dev=2):
    return ta.volatility.BollingerBands(pd.Series(df)).bollinger_lband()

class str(Strategy):
    # Any variables you want:
    ema_period = 200
    rsi_period = 14
    bol_period = 5
    bol_dev = 2
    def init(self):
        # Declare indicators you will use in the strategy:
        self.rsi = self.I(rsi, self.data.Close, self.rsi_period)
        self.macd = self.I(macd, self.data.Close)
        self.ema = self.I(ema, self.data.Close, self.ema_period)
        self.bol_h = self.I(bol_h, self.data.Close, self.bol_period, self.bol_dev)
        self.bol_l = self.I(bol_l, self.data.Close, self.bol_period, self.bol_dev)

    def next(self):
       price = self.data.Close[-1]
       if self.data.Close[-2] < self.bol_l[-2] and self.data.Close[-1] > self.bol_l[-1]:
            if not self.position:
                self.buy(size=0.1)
            if self.position.is_short:
                self.position.close()
                self.buy(size=0.1)
            if self.position.is_long:
                self.buy(size=0.1)
                
       if self.data.Close[-2] > self.bol_h[-2] and self.data.Close[-1] < self.bol_h[-1]:
            if not self.position:
                self.sell(size=0.1)
            if self.position.is_long:
                self.position.close()
                self.sell(size=0.1)
            if self.position.is_short:
                self.sell(size=0.1)


symbol = 'LAUSDT'
timeframe = '1m'
interval=1 #days

kl = klines_extended(symbol, timeframe, interval)
# cash is initial investment in USDT, margin is leverage (1/10 is x10)
# commission is about 0.07% for Binance Futures
bt = Backtest(kl, str, cash=100, margin=1/10, commission=0.0007, finalize_trades=True)

stats, heatmap = bt.optimize(
    bol_period = range(5,60,1),
    bol_dev=range(2, 4, 1),
    maximize='Equity Final [$]',
    max_tries=50000,
    random_state=0,
    return_heatmap=True,
)

print(stats)
bt.plot() 
result = pd.DataFrame(heatmap)
result.to_excel("heatmap.xlsx")