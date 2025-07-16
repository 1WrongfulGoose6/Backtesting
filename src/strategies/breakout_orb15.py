from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply
from datetime import time

import numpy as np
import pandas as pd
import pandas_ta as ta # Using panda's TA lib
from backtesting.test import GOOG #Google test data between 08/2004 -> 05/2009

def run(df):
    bt = Backtest(df, orb15, cash=100000, commission=.002, trade_on_close=True)
    stats = bt.run()
    return bt, stats


# trend indicators
def EMA9(x):
    return ta.ema(pd.Series(x), length=9).to_numpy()
def EMA21(x):
    return ta.ema(pd.Series(x), length=21).to_numpy()

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

# Opening Range Breakout Strategy which defines the range in the first 15min 
# Style: Breakout + volatility
class orb15(Strategy):

    def init(self):
        # Trend indicators
        self.ema9 = self.I(EMA9, self.data.Close)
        self.ema21 = self.I(EMA21, self.data.Close)
        
        # Momentum 
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

