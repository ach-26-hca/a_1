# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 16:12:10 2023

@author: ACHEW
"""

# Package Imports
import pandas as pd
import numpy as np

# Variable Delcerations
# Please change "USERNAME" to your respective username
deal_csv = "deal.csv"
price_csv = "price.csv"
convrate_csv = "convrate.csv"
fileDIR = "C:\\Users\\USERNAME\\Downloads\\"

# Import files in a DataFrame
deal_df = pd.read_csv(r"" + fileDIR + deal_csv)
price_df = pd.read_csv(r"" + fileDIR + price_csv)
conv_df = pd.read_csv(r"" + fileDIR + convrate_csv)


# Let user choose an integer to select the deal ID to retrieve, store the Index of selected deal in a variable
user_input = input("Enter Deal ID: ")
if user_input.isdigit():
    user_input = int(user_input)
else:
    raise ValueError("Please enter Deal ID as an integer")


# Some Quantity in "deal.csv" are in Metric Tons (MT), if it's the case on the selected deal, we want to convert it
# in Barrels (BBL). Each Index have a specific conversion rate (ex: HF38SG is very heavy, you need only 6.35 barrels to
# have 1 ton while the lighter NSG will need 9 barrels to weight 1 ton).
# Retrieve the Quantity in BBL if the selected deal is in Tons by multiplying Quantity in MT with convrate of
# matching index in conv_df (Be careful with M92FSG/M95FSG index in conv_df, we advise you to switch conv_df to a Serie)

# Create new columns within "deal_df"
deal_df["Conversion"] = np.nan
deal_df["QTY (BBL)"] = np.nan
deal_df = deal_df.replace(np.nan, 0)

# Split-up COL in "conv_df"
conv_df["M95FSG"] = conv_df["M92FSG/M95FSG"].apply(lambda x: pd.Series(str(x).split("/")))
conv_df = conv_df.rename(columns = {"M92FSG/M95FSG" : "M92FSG"})

# Ensuring "conv_df" variables are numerical
conv_df["M95FSG"] = pd.to_numeric(conv_df["M95FSG"], downcast = "float")

# Converting conv_df into series "conversions"
conversions = conv_df.squeeze()
conversions = conversions.tail(-1) 

# Mapping series "conversions" into respective COL values of "deal_df"
deal_df["Conversion"] = deal_df["Index"].map(conversions)

# Presenting "QTY (BBL)" COL values 
deal_df.loc[deal_df["Total Quantity (MT)"] > 0, "QTY (BBL)"] = deal_df["Total Quantity (MT)"] * deal_df["Conversion"]
deal_df.loc[deal_df["Total Quantity (BBL)"] > 0, "QTY (BBL)"] = deal_df["Total Quantity (BBL)"]

# Ensuring "deal_df" variables are numerical
deal_df = deal_df.astype({"Conversion" : np.float64, "QTY (BBL)" : np.float64})

# Ensuring "deal_df" Date COLs are all date format
deal_df[["Purchase From", "Purchase To", "Sales From", "Sales To"]] = \
deal_df[["Purchase From", "Purchase To", "Sales From", "Sales To"]] \
.apply(pd.to_datetime, format = "%d/%m/%Y")

for col in ["Purchase From", "Purchase To", "Sales From", "Sales To"]:
    deal_df[col] = deal_df[col].dt.date


# Retrieve and store the Pricing Period for Purchase and Sale of the deal, you will need it to calculate the average
# price later


# We will now work with the "price_df" where we assume all price are published in $/BBL.
# First, you should remove days without price published (weekend/holidays...).
# Be careful, HF38SG05 started to have quotes later than other index.

# Remove all rows where contains "NaN" from "price_df" of specified COLs
price_df.dropna(subset = ["GOR_SG", "M92FSG", "M95FSG", "NSG", "HF38SG", "HF38SG05"], how = "all", inplace = True)

# Convert date COL of "price_df" into date format for "price_df"
price_df["Dates"] = price_df["Dates"].apply(pd.to_datetime, format = "%d/%m/%Y")
price_df = price_df.set_index(pd.DatetimeIndex(price_df["Dates"]))
price_df["Dates"] = price_df["Dates"].dt.date

# Matching, Retrieving and Writing price values to respective columns in "deal_df" from "price_df"
deal_df["Purchase_1"] = None
for i, row_1 in deal_df.iterrows():
    date_val_1 = row_1["Purchase From"]
    index_value_1 = row_1["Index"]
    try:
        deal_df.loc[i, "Purchase_1"] = price_df.loc[price_df["Dates"] == date_val_1, index_value_1].item()
    except ValueError:
        deal_df.loc[i, "Purchase_1"] = None

deal_df["Purchase_2"] = None
for j, row_2 in deal_df.iterrows():
    date_val_2 = row_2["Purchase To"]
    index_value_2 = row_2["Index"]
    try:
        deal_df.loc[j, "Purchase_2"] = price_df.loc[price_df["Dates"] == date_val_2, index_value_2].item()
    except ValueError:
        deal_df.loc[j, "Purchase_2"] = None

deal_df["Sales_1"] = None
for k, row_3 in deal_df.iterrows():
    date_val_3 = row_3["Sales From"]
    index_value_3 = row_3["Index"]
    try:
        deal_df.loc[k, "Sales_1"] = price_df.loc[price_df["Dates"] == date_val_3, index_value_3].item()
    except ValueError:
        deal_df.loc[k, "Sales_1"] = None

deal_df["Sales_2"] = None
for l, row_4 in deal_df.iterrows():
    date_val_4 = row_4["Sales To"]
    index_value_4 = row_4["Index"]
    try:
        deal_df.loc[l, "Sales_2"] = price_df.loc[price_df["Dates"] == date_val_4, index_value_4].item()
    except ValueError:
        deal_df.loc[l, "Sales_2"] = None


# Retrieve the Purchase Price and Sale Price for the selected deal, it's the average of price during the pricing period
# on the deal index.

# Deriving average purchase price
def purchase_avg(row_5):
    return (row_5["Purchase_1"] + row_5["Purchase_2"])/2
deal_df["Purchase AVG"] = deal_df.apply(purchase_avg, axis = 1)

def sales_avg(row_6):
    return (row_6["Sales_1"] + row_6["Sales_2"])/2
deal_df["Sales AVG"] = deal_df.apply(sales_avg, axis = 1)


# You should now be able to display PnL of selected deal with formula:
# PnL = (Sold Price - Purchased Price) * Qty in BBL
# OPTIONAL: If you still have time, you can adapt your code to write directly the PnL in a new column at the end of
# "deal_df"

# Deriving PnL for each deal and presenting as separate COL within "deal_df"
def PNL(row_7):
    return((row_7["Sales AVG"] - row_7["Purchase AVG"]) * row_7["QTY (BBL)"])
deal_df["PnL"] = deal_df.apply(PNL, axis = 1)

# Rounding-off values as 4dp within "deal_df"
for col in ["Purchase AVG", "Sales AVG", "PnL"]:
    deal_df[col] = deal_df[col].round(4)

# Presenting user with selected Deal ID from "deal_df"
result = deal_df.loc[deal_df["Deal ID"] == user_input]
print(f"\n=========================\nSELECTED DEAL ID: {user_input} \
      \nINDEX: {result['Index'].iloc[0]} \
      \nAVG PURCHASE PX: {result['Purchase AVG'].iloc[0]} \
      \nAVG SALES PX: {result['Sales AVG'].iloc[0]} \
      \nQTY IN BBLS: {result['QTY (BBL)'].iloc[0]} \
      \nPnL FOR DEAL: {result['PnL'].iloc[0]} \
      ")

