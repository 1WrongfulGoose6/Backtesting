from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply
from datetime import time

import numpy as np
import pandas as pd
import pandas_ta as ta # Using panda's TA lib
from backtesting.test import GOOG #Google test data between 08/2004 -> 05/2009

# trend indicators
def EMA9(x):
    return ta.ema(pd.Series(x), length=9).to_numpy()
def EMA21(x):
    return ta.ema(pd.Series(x), length=21).to_numpy()
def SuperTrend(high, low, close):
    df = ta.supertrend(high=pd.Series(high),
                       low=pd.Series(low),
                       close=pd.Series(close),
                       length=10,
                       multiplier=3.0)
    
    if df is None or df.empty:
        return np.full_like(close, np.nan)
    
    # Return only the Supertrend line (this is aligned with price)
    return df['SUPERT_10_3.0'].to_numpy()

def HullMovingAvg(close):
     return ta.hma(close, length=22)
def BollingerBands(Close):
    bb = ta.bbands(Close, length=22, std=2)
    if bb is not None:
            return bb['BBL_20_2.0'].to_numpy(), bb['BBM_20_2.0'].to_numpy(), bb['BBU_20_2.0'].to_numpy()
    else:
        # Return NaN arrays of the same length if BBs can't be calculated yet
        n = len(Close)
        return [float('nan')] * n, [float('nan')] * n, [float('nan')] * n
def Ichimoku(high, low, close):
    ichimoku_tuple = ta.ichimoku(pd.Series(high), pd.Series(low),pd.Series(close))

    if ichimoku_tuple is not None and len(ichimoku_tuple) == 5:
        senkou_a, senkou_b, tenkan_sen, kijun_sen, chikou_span = ichimoku_tuple
        return (
            senkou_a.to_numpy(),  # Span A (Leading line 1)
            senkou_b.to_numpy(),  # Span B (Leading line 2)
            tenkan_sen.to_numpy(),  # Conversion line
            kijun_sen.to_numpy(),  # Base line
            chikou_span.to_numpy()  # Lagging span
        )
    else:
        # fallback if not enough data
        n = len(close)
        return (
            [float('nan')] * n,
            [float('nan')] * n,
            [float('nan')] * n,
            [float('nan')] * n,
            [float('nan')] * n,
        )

  
# momentum indicators
def RSI(x):
    return ta.rsi(pd.Series(x), length=14).to_numpy()
def MACDLine(x):
    return ta.macd(pd.Series(x))['MACD_12_26_9'].to_numpy()
def MACDHist(x):
    return ta.macd(pd.Series(x))['MACDh_12_26_9'].to_numpy()
def MACDSig(x):
    return ta.macd(pd.Series(x))['MACDs_12_26_9'].to_numpy()
def StochRSI(x):
    rsi_df = ta.stochrsi(pd.Series(x))
    return rsi_df['STOCHRSIk_14_14_3_3'].to_numpy(), rsi_df['STOCHRSId_14_14_3_3'].to_numpy()

# volatility indicators
def ADX(High, Low, Close):
    return ta.adx(pd.Series(High), pd.Series(Low), pd.Series(Close))

# volume indicators
def VWAP(high, low, close, volume):
    idx = VWAP.df_index[:len(close)]
    h = pd.Series(high, index=idx)
    l = pd.Series(low, index=idx)
    c = pd.Series(close, index=idx)
    v = pd.Series(volume, index=idx)

    vwap_series = ta.vwap(high=h, low=l, close=c, volume=v)
    return vwap_series.to_numpy()
def DailyPOC(df):
    df = df.copy()
    df['Date'] = df.index.date
    poc_list = []

    for date, group in df.groupby('Date'):
        # Use close prices or better: price buckets with volume sum
        most_common_price = group['Close'].round(2).mode()
        poc_value = most_common_price.iloc[0] if not most_common_price.empty else np.nan
        poc_list.extend([poc_value] * len(group))

    return np.array(poc_list)
def POC_2hour(df):
    df = df.copy()
    df['TimeBin'] = df.index.floor('2H')  # Floor to the nearest 2-hour window
    poc_list = []

    for time_bin, group in df.groupby('TimeBin'):
        most_common_price = group['Close'].round(2).mode()
        poc_value = most_common_price.iloc[0] if not most_common_price.empty else np.nan
        poc_list.extend([poc_value] * len(group))

    return np.array(poc_list)

def badTimeToTrade(current_time):
    # Return True if NOT in the trading window
    if time(9, 30) <= current_time <= time(13, 15):
        return False  # Good time to trade
    return True  # Outside trading window → skip

class emaCross(Strategy):

    def init(self):
        # Trend indicators
        self.ema9 = self.I(EMA9, self.data.Close)
        self.ema21 = self.I(EMA21, self.data.Close)
        self.bb_lower, self.bb_mid, self.bb_upper = self.I(BollingerBands, self.data.Close)
        self.hma = self.I(BollingerBands, self.data.Close)
        self.ichi_a, self.ichi_b, self.tenkan, self.kijun, self.chikou = self.I(Ichimoku, self.data.High, self.data.Low, self.data.Close)
        self.SuperTrend = self.I(SuperTrend, self.data.High, self.data.Low, self.data.Close)
        
        # Momentum indicators/oscilators
        self.rsi = self.I(RSI, self.data.Close)
        self.macd = self.I(MACDLine, self.data.Close) #macd has 3 signals 
        self.macd_hist = self.I(MACDHist, self.data.Close)
        self.macd_signal = self.I(MACDSig, self.data.Close)
        self.stoch_k, self.stoch_d = self.I(StochRSI, self.data.Close)
        
        self.atr = self.I(lambda h, l, c: ta.atr(pd.Series(h), pd.Series(l), pd.Series(c), length=14).to_numpy(), self.data.High, self.data.Low, self.data.Close)
        
        VWAP.df_index = self.data.df.index  # make sure your index is datetime!
        self.vwap = self.I(VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        self.poc = self.I(DailyPOC,self.data.df)
        self.poc = self.I(POC_2hour,self.data.df)

        self.adx = self.I(ADX, self.data.High, self.data.Low, self.data.Close)

    def next(self):
        # close old order and buy long
        if pd.isna(self.ema9[-1]) or pd.isna(self.ema21[-1]):
            return
        # current_index = len(self.data.Close) - 1
        # self.htfBullish = self.data.df['HTFSig'].iloc[current_index]
        current_time = self.data.df.index[len(self.data.Close) - 1].time()
        
        # if badTimeToTrade(current_time):
        #     return  # Skip this candle
        
        current_adx = self.adx[-1]  # current ADX value
        if current_adx < 20:
        # skip or reduce position size because of weak trend
            return

        # Long
        if crossover(self.ema9, self.ema21):
            # if (self.htfBullish):
                stoploss = self.data.Close[-1] - self.atr[-1]
                takeprofit = self.data.Close[-1] + 2 * self.atr[-1]
                self.buy(sl=stoploss, tp=takeprofit, size=1)
                print("\n",f"Long Entered {current_time} with sl:{stoploss:.2f}, tp:{takeprofit:.2f}")

        # Short
        elif crossover(self.ema21, self.ema9):
            # if not (self.htfBullish):
                stoploss = self.data.Close[-1] + self.atr[-1]
                takeprofit = self.data.Close[-1] - 2 * self.atr[-1]
                print("\n",f"Short Entered {current_time} with sl:{stoploss:.2f}, tp:{takeprofit:.2f}")
                self.sell(sl=stoploss, tp=takeprofit, size=1)


# Give user option to change file names
# path = input("Please enter file name (with csv): ")
path = "SPY_2025-06-13_2025-06-16.csv"
# "SPY_2024-01-01_2024-01-04.csv" --sample file
# "SPY_2025-03-09_2025-03-14.csv"
ltfData = pd.read_csv(path, parse_dates=['timestamp'])
ltfData.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 
                       'close': 'Close', 'volume': 'Volume'}, inplace=True)
ltfData.set_index('timestamp', inplace=True)

# for resampling data into Higher Time Frame 
ltfData = ltfData.between_time("9:30", "16:00")
htfData = ltfData.resample('1h').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

# Recreate EMA's and convert them into a signal for the Lower Time Frame df using reindexing
htfData['EMA9']= ta.ema(htfData['Close'], length=9)
htfData['EMA21']= ta.ema(htfData['Close'], length=21)
htfData.dropna(subset=["EMA9", "EMA21"], inplace=True)
htfData['HTFSignal'] = htfData['EMA9'] > htfData['EMA21']
ltfData['HTFSig'] = htfData['HTFSignal'].reindex(ltfData.index, method='ffill')

bt = Backtest(ltfData, emaCross, cash=100000, commission=.002, trade_on_close=True)
output = bt.run()
bt.plot()
print(output)

# print(htfData)
# print(ltfData)