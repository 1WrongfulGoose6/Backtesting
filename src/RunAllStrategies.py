import os
import pandas as pd
from datetime import datetime
from strategies import strategy1, EmaCrossOver

# path = input("Please enter file name (with csv): ")
# path = "SPY_2025-03-09_2025-03-14.csv"
# "SPY_2024-01-01_2024-01-04.csv" --sample file
df = pd.read_csv('data\AMD\AMD_2025-06-01_2025-06-06.csv', parse_dates=True, index_col='timestamp')
df.dropna(inplace=True)

df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 
                       'close': 'Close', 'volume': 'Volume'}, inplace=True)


timestamp = datetime.now().strftime("%Y%m%d_%H%m")
output_dir = f"outputs/results_{timestamp}"
os.makedirs(output_dir, exist_ok=True)

strategies = {
    "EMA9/21": EmaCrossOver.run,
    "Bolinger": strategy1.run
}

# for each name/fn in dict
for name, strategy_fn in strategies.items():
    bt, stats = strategy_fn(df.copy())
    html_path = os.path.join(output_dir, f"{name}_result.html")
    print(f"Saving {name} result to {html_path}")
    bt.plot(filename=html_path)
    stats.to_csv(os.path.join(output_dir, f"{name}_stats.csv"))

