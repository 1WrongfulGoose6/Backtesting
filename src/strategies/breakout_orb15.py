from backtesting import Backtest, Strategy
from datetime import time

import numpy as np
import pandas as pd
import pandas_ta as ta # Using panda's TA lib
from backtesting.test import GOOG #Google test data between 08/2004 -> 05/2009

def run(df):

    df = find_opening_range(df)
    bt = Backtest(df, orb15, cash=100000, commission=.002, trade_on_close=True)
    stats = bt.run()
    return bt, stats

def find_opening_range(df):
    df['date'] = df.index.date
    df['ORB_high'] = None
    df['ORB_low'] = None
    for day, day_df in df.groupby('date'):
        opening_range = day_df.between_time("9:30", "9:45")
        orb_high = opening_range['High'].max()
        orb_low = opening_range['Low'].min()

        df.loc[day_df.index, 'ORB_high'] = orb_high
        df.loc[day_df.index, 'ORB_low'] = orb_low

    return df

def bad_to_trade(current_time):
    if time(9,45) <= current_time <= time(12,00):
        return False
    return True

# Opening Range Breakout Strategy which defines the range in the first 15min 
# Style: Breakout + volatility
class orb15(Strategy):

    def init(self):

        # Momentum 
        self.atr = self.I(lambda h, l, c: ta.atr(pd.Series(h), pd.Series(l), pd.Series(c), length=14).to_numpy(), self.data.High, self.data.Low, self.data.Close)
        self.last_traded_date = None

    def next(self):
        price = self.data.Close[-1]
        current_time = self.data.df.index[len(self.data.Close) - 1].time()
        current_date = self.data.df.index[len(self.data.Close)-1].date()

        if bad_to_trade(current_time):
            if self.position:
                self.position.close()
            return
        
        if self.last_traded_date == current_date:
            return

        if self.data.ORB_high[-1] < price and not self.position:
             sl = price - 10 * self.atr[-1]
             tp = price + 20 * self.atr[-1]
             self.buy(sl=sl, tp=tp, size=1)
             self.last_traded_date = current_date
        
        if self.data.ORB_low[-1] > price and not self.position:
             sl = price + 10* self.atr[-1]
             tp = price - 20 * self.atr[-1]
             self.sell(sl=sl, tp=tp, size=1)
             self.last_traded_date = current_date
        


