from datetime import datetime, timedelta

import pandas as pd
import glob
import os


symbol = input("Enter Ticker Name: ")
csv_files = glob.glob(fr"E:\Ashwin\importantFiles\Programming Projects\Backtesting\data\{symbol}\{symbol}*.csv", recursive=True)
folder_path = f"E:\Ashwin\importantFiles\Programming Projects\Backtesting\data\{symbol}"

print("Matched files:", csv_files)
# Create list to store all dfs into and parse timestamp column as datetime
dfs = []
for file in csv_files:
    print("Reading:", file)
    df = pd.read_csv(file, parse_dates=['timestamp'])  # 'timestamp' column assumed
    dfs.append(df)

# Concat to append all dataframes together and drop duplicate data (duplicate timestamps)
if not dfs:
    print("No files found for symbol:", symbol)
else:
    print("Merging all CSVs...")
    merged_df = pd.concat(dfs)
    merged_df = merged_df.drop_duplicates(subset='timestamp')   

    # Sort by time to ensure chronological order and save to a new csv file
    merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)
    merged_filename = os.path.join(folder_path, f"{symbol}_merged_data.csv")
    merged_df.to_csv(merged_filename, index=False)

    print("Bulk file succesfully saved as", f"{symbol}_merged_data.csv")

    
    