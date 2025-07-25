from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply
from datetime import time

import numpy as np
import pandas as pd
import pandas_ta as ta # Using panda's TA lib
from backtesting.test import GOOG #Google test data between 08/2004 -> 05/2009

def run(df):
    bt = Backtest(df, bollinger_breakout, cash=100000, commission=.000, trade_on_close=True)
    stats = bt.run()
    return bt, stats

# delcaring all indicator functions to be used during simulation
def BollingerBands(Close):
    Close = pd.Series(Close)
    bb = ta.bbands(Close, length=20, std=2)

    if bb is None or bb.isnull().all().any():
        # Return 3 NaN arrays of same length
        n = len(Close)
        return np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)

    return (
        bb['BBL_20_2.0'].to_numpy(),
        bb['BBM_20_2.0'].to_numpy(),
        bb['BBU_20_2.0'].to_numpy()
    )

def RSI(x):
    return ta.rsi(pd.Series(x), length=14).to_numpy()

def bad_to_trade(current_time):
    if time(9,30) <= current_time <= time(12,00):
        return False
    return True

# Breakout Strategy which defines the range in BB bars  
# Style: Breakout + volatility
class bollinger_breakout(Strategy):

    def init(self):
        # Trend indicators
        self.bb_lower = self.I(lambda x: BollingerBands(x)[0], self.data.Close)
        self.bb_mid = self.I(lambda x: BollingerBands(x)[1], self.data.Close)
        self.bb_upper = self.I(lambda x: BollingerBands(x)[2], self.data.Close)
        self.rsi = self.I(RSI, self.data.Close)
        
    def next(self):
        current_index = len(self.data.Close) - 1
        current_time = self.data.df.index[len(self.data.Close) - 1].time()
        price = self.data.Close[-1]

        if bad_to_trade(current_time):
            if self.position:
                self.position.close()
            return
        
        # check if in squeeze
        lower = self.bb_lower[-1]
        middle = self.bb_mid[-1]
        upper = self.bb_upper[-1]

        if any(pd.isna([lower, middle, upper])):
            return
        
        bb_width = self.bb_upper[-20:] - self.bb_lower[-20:]
        current_width = upper - lower
        min_width = bb_width.min()

        if current_width <= min(bb_width)  and not self.position:
            if price > upper and self.rsi > 50 and self.data.Volume[-1] > 20000:
                risk = 1.5 * current_width  # dynamic based on market
                sl = price - risk
                tp = price + 2 * risk  # aim for 1:1.3 to 1:2 RRR
                self.buy(sl=sl, tp=tp, size=1)

        elif current_width <= min(bb_width) and not self.position:
            if price < lower and self.rsi < 50 and self.data.Volume[-1] > 20000:
                risk = 1.5 * current_width  # dynamic based on market
                sl = price + risk
                tp = price - 2 * risk  # aim for 1:1.3 to 1:2 RRR
                self.sell(sl=sl, tp=tp, size=1)

     

