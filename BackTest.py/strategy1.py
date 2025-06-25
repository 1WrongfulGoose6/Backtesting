from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.lib import resample_apply

import pandas as pd
import pandas_ta as ta # Using panda's TA lib
from backtesting.test import GOOG #Google test data between 08/2004 -> 05/2009

# delcaring all indicator functions to be used during simulation
def EMA9(x):
    return ta.ema(pd.Series(x), length=9).to_numpy()
def EMA21(x):
    return ta.ema(pd.Series(x), length=21).to_numpy()
def RSI(x):
    return ta.rsi(pd.Series(x), length=14).to_numpy()
def MACDLine(x):
    return ta.macd(pd.Series(x))['MACD_12_26_9'].to_numpy()
def MACDHist(x):
    return ta.macd(pd.Series(x))['MACDh_12_26_9'].to_numpy()
def MACDSig(x):
    return ta.macd(pd.Series(x))['MACDs_12_26_9'].to_numpy()


class emaCross(Strategy):

    def init(self):
        # Trend indicators
        self.ema9 = self.I(EMA9, self.data.Close)
        self.ema21 = self.I(EMA21, self.data.Close)

        # Momentum indicators/oscilators
        self.rsi = self.I(RSI, self.data.Close)
        self.macd = self.I(MACDLine, self.data.Close) #macd has 3 signals 
        self.macd_hist = self.I(MACDHist, self.data.Close)
        self.macd_signal = self.I(MACDSig, self.data.Close)

    def next(self):
        # close old order and buy long
        if pd.isna(self.ema9[-1]) or pd.isna(self.ema21[-1]):
            return
        current_index = len(self.data.Close) - 1
        self.htfBullish = self.data.df['HTFSig'].iloc[current_index]
        price = self.data.Close[-1]
        sl_pct = 0.03  # 2% Stop Loss
        tp_pct = 0.15  # 4% Take Profit
        trail_amount = 1.0 
    

        if crossover(self.ema9, self.ema21):
            self.position.close()
            if (self.htfBullish):
                print("True condition triggerd")
                stoploss = price * (1-sl_pct)
                takeprofit = price * (1 + tp_pct)
                self.buy(sl=stoploss, tp=takeprofit)

        # close old order and buy short
        elif crossover(self.ema21, self.ema9):
            self.position.close()
            if not (self.htfBullish):
                print("False condition triggerd")
                stoploss = price * (1 + sl_pct)
                takeprofit = price * (1 - tp_pct)
                self.sell(sl=stoploss, tp=takeprofit)

# Give user option to change file names
# path = input("Please enter file name (with csv): ")
path = "SPY_2024-01-01_2024-01-04.csv"
# "SPY_2024-01-01_2024-01-04.csv" --sample file
ltfData = pd.read_csv(path, parse_dates=['timestamp'])
ltfData.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 
                       'close': 'Close', 'volume': 'Volume'}, inplace=True)
ltfData.set_index('timestamp', inplace=True)

# for resampling data into Higher Time Frame 
htfData = ltfData.resample('30min').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

# Recreate EMA's and convert them into a signal for the Lower Time Frame df using reindexing
htfData['EMA9']= ta.ema(htfData['Close'], length=9)
htfData['EMA21']= ta.ema(htfData['Close'], length=21)
htfData['HTFSignal'] = htfData['EMA9'] > htfData['EMA21']
ltfData['HTFSig'] = htfData['HTFSignal'].reindex(ltfData.index, method='ffill')

bt = Backtest(ltfData, emaCross, cash=1000, commission=.002)
output = bt.run()
bt.plot()

# print(htfData)
# print(ltfData)