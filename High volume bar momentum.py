# -*- coding: utf-8 -*-
"""
Created on Tue Dec 28 12:27:47 2021

@author: Richard
"""

import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from datetime import date
from datetime import datetime
from dateutil import parser
from statsmodels.graphics.tsaplots import plot_acf
from collections import Counter

tickers = ["EVO", "SINCH", "LATO_B", "KINV_B", "NIBE_B", "EQT", "MIPS", "STORY_B", "SF", "PDX", "SBB_B", "BALD_B", "SAGA_B"]
long_short_returns = {}

for x in tickers:
    data = pd.read_csv('OMXSTO_DLY_'+x+', 15.csv')
    
    time_offset_removed =  data["time"].str[:-6]
    only_date_part = data["time"].str[:-15]
    only_time_part = time_offset_removed.str[11:]
        
    data.insert(1,"DatePart", only_date_part) 
    data.insert(2,"TimePart", only_time_part)
    
    #Closing prices for the trading session, full and half session
    full_day_dates = data[data["TimePart"] == "17:15:00"]["DatePart"].to_frame()
    all_dates =  data[data["TimePart"] == "09:00:00"]["DatePart"].to_frame()
    idx = np.where(all_dates.merge(full_day_dates,how="left",indicator=True)["_merge"] == "left_only")
    half_day_dates = all_dates.iloc[idx]["DatePart"].to_frame()
    half_days_data = data[data["DatePart"].isin(half_day_dates["DatePart"])]
    half_days_data["TimePart"] == "12:45:00"
    
    #EXIT PRICES for both half and full sessions
    exit_price_half_day = half_days_data[half_days_data["TimePart"] == "12:45:00"]["close"]
    exit_price_full_days = data[data["TimePart"] == "17:15:00"]["close"]
    exit_price = exit_price_full_days.append(exit_price_half_day)
    
    exit_price = exit_price.sort_index()
    exit_price = exit_price.to_frame().astype(float)
    exit_price.insert(1,"DatePart",only_date_part)
    exit_price = exit_price.set_index("DatePart")
    
    
    volume = data.groupby(["DatePart"]).sum()["Volume"]
    adv = volume.rolling(20).mean().shift(1)
    
    high_volume_bar = data["Volume"] > 10*data["Volume"].rolling(1000).mean().shift(1)
    bar_return = data["close"]/data["open"]-1
    not_open = (data["TimePart"] != "09:00:00") & (data["TimePart"] != "09:15:00") 
    not_close = (data["TimePart"] != "17:15:00") & (data["TimePart"] != "17:00:00")
    
    long_pos_ind = (bar_return > 0) & high_volume_bar & not_open & not_close
    short_pos_ind = (bar_return < 0) & high_volume_bar & not_open & not_close
    
    long_exit_ind = long_pos_ind.shift(4).fillna(False)
    short_exit_ind = short_pos_ind.shift(4).fillna(False)
    
    
    # long_pos_ind = long_pos_ind.to_frame()
    # long_pos_ind.insert(1,"DatePart",only_date_part)
    # long_pos_ind = long_pos_ind.set_index("DatePart")
    # long_pos_ind.columns = ["pos indicator"]
    
    # short_pos_ind = short_pos_ind.to_frame()
    # short_pos_ind.insert(1,"DatePart",only_date_part)
    # short_pos_ind = short_pos_ind.set_index("DatePart")
    # short_pos_ind.columns = ["pos indicator"]
    #long_entry_price = data[long_pos_ind]["close"].astype(float)
    long_entry_price = (data[long_pos_ind]["open"].astype(float) + data[long_pos_ind]["close"].astype(float) + data[long_pos_ind]["low"].astype(float) + data[long_pos_ind]["high"].astype(float))/4 
    short_entry_price = (data[short_pos_ind]["open"].astype(float) +data[short_pos_ind]["close"].astype(float) + data[short_pos_ind]["low"].astype(float) + data[short_pos_ind]["high"].astype(float))/4
    #short_entry_price = data[short_pos_ind]["close"].astype(float)
    # long_dates = data.iloc[long_entry_price.index]["DatePart"]
    # long_exit_idx = exit_price.index.isin(long_dates)
    # long_exit_price = exit_price[long_exit_idx].astype(float)
    
    # short_dates = data.iloc[short_entry_price.index]["DatePart"]
    # short_exit_idx = exit_price.index.isin(short_dates)
    # short_exit_price = exit_price[short_exit_idx]
    long_exit_price = data[long_exit_ind]["close"].astype(float) 
    short_exit_price = data[short_exit_ind]["close"].astype(float)
    
    #calculate returns
    comm = 0.0002
    slippage = 0.1/100
    long_strat_returns = long_exit_price.div(long_entry_price.values)-1-comm*2-slippage
    short_strat_returns = -(short_exit_price.div(short_entry_price.values)-1)-comm*2-slippage
    
    combined_long_short = pd.concat([long_strat_returns, short_strat_returns],axis=0)
    #combined_long_short = combined_long_short.sort_index()
    #combined_long_short = combined_long_short.to_frame()
    long_short_returns.update(combined_long_short)



returns = pd.DataFrame(list(long_short_returns.items()),columns=["index", "returns"])
returns = returns.set_index("index")
returns = returns.sort_index()

#
print("avg return " + str(returns["returns"].mean()))
print("volatility " + str(returns["returns"].std()))
#
kelly_f = returns["returns"].mean()/(returns["returns"].std()**2)
print("kelly f " + str(kelly_f))
percent_profitable = (returns["returns"] > 0).sum()/len(returns["returns"])
print("Percent profitable " + str(percent_profitable))
#
#
#
#############################################
###stats for basic strategy
############################################
cum_ret =(1 + returns["returns"]).cumprod()
total_return = cum_ret.tail(1)-1
print("Total return " + str(total_return))
print("Number of trades " + str(len(returns["returns"])))
#
#
#long_kelly_f = long_strat_returns.mean()/long_strat_returns.std()**2
#short_kelly_f = short_strat_returns.mean()/short_strat_returns.std()**2
#
#print("Long kelly " + str(long_kelly_f))
#print("Short kelly " + str(short_kelly_f))
#
#
###plots
plt.plot(cum_ret)
