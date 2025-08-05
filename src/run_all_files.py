import os
import pandas as pd
from datetime import datetime
from strategies import breakout_orb15, breakout_bollinger, master_file, mean_reversion_vwap


# "data\QQQ\QQQ_merged_data.csv" --sample file
# "data\AMD\AMD_merged_data.csv" --sample file
# "data\SPY\SPY_merged_data.csv" --sample file
# "data\SOFI\SOFI_merged_data.csv" --sample file
# "data\KO\KO_merged_data.csv" --sample file

df = pd.read_csv('data\SOFI\SOFI_merged_data.csv', parse_dates=True, index_col='timestamp')
df.dropna(inplace=True)

df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 
                       'close': 'Close', 'volume': 'Volume'}, inplace=True)

df = df.resample('5min').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_dir = f"outputs/results_{timestamp}"
os.makedirs(output_dir, exist_ok=True)

strategies = {
    # "EMA9/21": master_file.run,
    # "ORB15": breakout_orb15.run,
    "VWAP Reversion" : mean_reversion_vwap.run
    # "Bollinger_Squeeze" : breakout_bollinger.run
}

# for each name/fn in dict
for name, strategy_fn in strategies.items():
    bt, stats = strategy_fn(df.copy())
    html_path = os.path.join(output_dir, f"{name}_result.html")
    print(f"Saving {name} result to {html_path}")
    bt.plot(filename=html_path)
    stats.to_csv(os.path.join(output_dir, f"{name}_stats.csv"))

