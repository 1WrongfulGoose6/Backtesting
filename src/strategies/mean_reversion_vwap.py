from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply
from datetime import time

import numpy as np
import pandas as pd
import pandas_ta as ta # Using panda's TA lib
from backtesting.test import GOOG #Google test data between 08/2004 -> 05/2009

def run(df):
    bt = Backtest(df, vwap_reversion, cash=100000, commission=.000, trade_on_close=True)
    stats = bt.run()
    return bt, stats


# momentum indicators
def RSI(x):
    return ta.rsi(pd.Series(x), length=14).to_numpy()

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

def POC_2hour(df):
    df = df.copy()
    df['TimeBin'] = df.index.floor('2H')  # Floor to the nearest 2-hour window
    poc_list = []

    for time_bin, group in df.groupby('TimeBin'):
        most_common_price = group['Close'].round(2).mode()
        poc_value = most_common_price.iloc[0] if not most_common_price.empty else np.nan
        poc_list.extend([poc_value] * len(group))

    return np.array(poc_list)

def bad_to_trade(current_time):
    if time(9,30) <= current_time <= time(12,00):
        return False
    return True

# Price reverts towards VWAP after being oversold/bought on RSI
# Style: Mean reversion
class vwap_reversion(Strategy):

    def init(self):

        # Momentum indicators/oscilators
        self.rsi = self.I(RSI, self.data.Close)
        
        self.atr = self.I(lambda h, l, c: ta.atr(pd.Series(h), pd.Series(l), pd.Series(c), length=14).to_numpy(), self.data.High, self.data.Low, self.data.Close)
        
        VWAP.df_index = self.data.df.index  # make sure your index is datetime!
        self.vwap = self.I(VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)
        # self.poc = self.I(POC_2hour,self.data.df)

        self.adx = self.I(ADX, self.data.High, self.data.Low, self.data.Close)

    def next(self):
        current_index = len(self.data.Close) - 1
        current_time = self.data.df.index[len(self.data.Close) - 1].time()
        price = self.data.Close[-1]
        vwap = self.vwap[-1]
        rsi = self.rsi[-1]

        if current_time > time(2,30) and self.position:
            self.position.close()
         
        if self.position:
            if (self.position.is_long and price >= vwap) or (self.position.is_short and price <= vwap):
                self.position.close()

        # Only buy during awake hrs 
        if not bad_to_trade(current_time):
            # Long
            if price < vwap * 0.997 and rsi < 35 and not self.position:
                self.buy(sl=price - 0.5, tp=price + 1.0)

            # Short
            elif price > vwap * 1.007 and rsi > 65 and not self.position:
                self.sell(sl=price + 0.5, tp=price - 1.0)
