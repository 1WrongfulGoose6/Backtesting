from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply
from datetime import time

import pandas as pd
import pandas_ta as ta # Using panda's TA lib
from backtesting.test import GOOG #Google test data between 08/2004 -> 05/2009

def run(df):
    bt = Backtest(df, bollinger_breakout, cash=100000, commission=.002, trade_on_close=True)
    stats = bt.run()
    return bt, stats

# delcaring all indicator functions to be used during simulation
def BollingerBands(Close):
    bb = ta.bbands(Close, length=22, std=2)
    if bb is not None:
            return bb['BBL_20_2.0'].to_numpy(), bb['BBM_20_2.0'].to_numpy(), bb['BBU_20_2.0'].to_numpy()
    else:
        # Return NaN arrays of the same length if BBs can't be calculated yet
        n = len(Close)
        return [float('nan')] * n, [float('nan')] * n, [float('nan')] * n

def badTimeToTrade(current_time):
    # Return True if NOT in the trading window
    if time(9, 30) <= current_time <= time(13, 15):
        return False  # Good time to trade
    return True  # Outside trading window → skip


class bollinger_breakout(Strategy):

    def init(self):
        # Trend indicators
        self.bb = self.I(BollingerBands, self.data.Close)
        
    def next(self):
        # close old order and buy long
        if pd.isna(self.ema9[-1]) or pd.isna(self.ema21[-1]):
            return
        current_index = len(self.data.Close) - 1
        self.htfBullish = self.data.df['HTFSig'].iloc[current_index]
        current_time = self.data.df.index[len(self.data.Close) - 1].time()
        price = self.data.Close[-1]


        if current_time >= pd.to_datetime("13:15").time():
            if self.position:
                print("Overnight Position closed.")
                self.position.close()

        # current_time = self.data.df.index[self.i].time()
        if badTimeToTrade(current_time):
            print("Skipping", current_time, "due to outside trading window.")
            return  # Skip this candle
        else:
            print("Trading at", current_time)

        if crossover(self.ema9, self.ema21):
            self.position.close()
            if (self.htfBullish):
                print("Bullish condition triggerd")
                self.buy()

        # close old order and buy short
        elif crossover(self.ema21, self.ema9):
            self.position.close()
            if not (self.htfBullish):
                print("Bearish condition triggerd")
                self.sell()

