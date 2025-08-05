from polygon import RESTClient #Using polgyon.io's minute aggr data
from datetime import datetime, timedelta

import pandas as pd
import time
import os


# Connecting to Polygon.io API using API Key (extracted from a txt file)
file = 'polygon_api_key.txt'
with open(file, 'r') as file:
    API_KEY = file.read().strip()
client = RESTClient(API_KEY)


# Function to download min data in a chunk and save to csv file
def fetch_and_save(symbol, from_data, to_date, filename):
    bars = []
    for bar in client.list_aggs(ticker=symbol, multiplier=1, timespan="minute", from_=from_data, to=to_date, limit=5000):
        
        bars.append({
            "timestamp": pd.to_datetime(bar.timestamp, unit="ms"),
            "open": bar.open,
            "high": bar.low,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        })

    # converting list into valid df before saving
    df = pd.DataFrame(bars)
    df.to_csv(filename)
    print(f"Saved: {filename}")
    return df

# Take input from user and validate date format 
while True:
    symbol = str(input("Enter the Symbol you want to fetch: ")).upper() #e.g.SPY
    startString = input("Enter the start date in dd/mm/yyyy: ") #e.g.(16/6/2024)
    endString = input("Enter the end date in dd/mm/yyyy: ")
    delta = timedelta(days=int((input("Enter the chunks of data (in days): ")))) #e.g.5 days
    try:
        start = datetime.strptime(startString, "%d/%m/%Y")
        end = datetime.strptime(endString, "%d/%m/%Y")
        break
    except:
        print("invalid date or dates. Please use dd/mm/yyyy format\n")

# Confirm user input
print("You want to fetch 1m aggregate data of", symbol, "from", start.date(), "to", end.date(), "in chunks of", delta.days, "days. Type Yes to continue or No to exit")
response = str(input())
response = response.strip().lower()

folder_path = f"E:/Ashwin/importantFiles/Programming Projects/Backtesting/data/{symbol}/"
os.makedirs(folder_path, exist_ok=True)


if (response == "no"):
    print("exiting...\n")
    exit()
elif(response == "yes"):
    print("fetching...\n")
else:
    print("unrecognised input, exiting...")
    exit()


# Loops chunks from start date to end date, updating chunk_end as the latest data point
while start< end:
    chunk_end = start + delta
    if chunk_end > end:
        chunk_end = end
    
    # create csv file to store chunk data and then update the start time.
    filename = os.path.join(folder_path, f"{symbol}_{start.date()}_{chunk_end.date()}.csv")
    fetch_and_save(symbol, str(start.date()), str(chunk_end.date()), filename)
    start = chunk_end + timedelta(days=1) # skip to the next when starting the next chunk
    time.sleep(15)  # To respect 5 calls/minute limit
print("Data transfer completed.\n")
