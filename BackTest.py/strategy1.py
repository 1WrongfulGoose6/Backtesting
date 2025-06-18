from backtesting import Backtest, Strategy
from backtesting.lib import crossover

import pandas as pd
import pandas_ta as ta # Using panda's TA lib
import numpy as np

from backtesting.test import GOOG #Google test data between 08/2004 -> 05/2009



# calculate indicators and add them as columns
GOOG['EMA9'] = GOOG.ta.ema(length=9)
GOOG['EMA21'] = GOOG.ta.ema(length=21)



class emaCross(Strategy):

    def init(self):
        close_series = pd.Series(self.data.Close)
        self.ema9 = self.I(lambda x: ta.ema(pd.Series(x), length=9).to_numpy(), self.data.Close)
        self.ema21 = self.I(lambda x: ta.ema(pd.Series(x), length=21).to_numpy(), self.data.Close)
        # self.ema21 = self.data.df['EMA21']

    def next(self):
        # close old order and buy long
        if pd.isna(self.ema9[-1]) or pd.isna(self.ema21[-1]):
            return
        price = self.data.Close[-1]
        sl_pct = 0.03  # 2% Stop Loss
        tp_pct = 0.15  # 4% Take Profit
        trail_amount = 1.0 
    

        
        if crossover(self.ema9, self.ema21):
            self.position.close()
            stoploss = price * (1-sl_pct)
            takeprofit = price * (1 + tp_pct)
            self.buy()
        # close old order and buy short
        elif crossover(self.ema21, self.ema9):
            self.position.close()
            stoploss = price * (1 + sl_pct)
            takeprofit = price * (1 - tp_pct)
            self.sell()
            
bt = Backtest(GOOG, emaCross, cash=1000, commission=.002)
output = bt.run()
bt.plot()
print(output)
# print(GOOG)
        

