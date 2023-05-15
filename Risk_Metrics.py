import pandas as PD;
import numpy as NP;
import math;

def Stats_on_csv(input_file, lookback_period, holding_period, confidence_level, business_days=252):
    """
    It calculates Value-at-Risk at the given confidence level for given look-back and holding periods.
    Look-back period is in years and holding_period is in days. It assumes 252 business days in a year.
    The input file is in csv format retrieved from Yahoo! Finance. Column format:
    Date | Open | High | Low | Close | Adj. close | Volume
    VaR is given in % calculated on the worst log returns in the holding period.
    """
    #################### Input checks: ####################
    if (type(input_file) != str):
        print("The input file name must be a string!");
        return None;
    
    if (type(holding_period) != int):
        print("The holding period must be an integer!");
        return None;

    if (type(business_days) != int):
        print("The business days number must be an integer!");
        return None;
    
    if (holding_period > 10 or holding_period < 1): # arbitrary ceiling of 10 days
        print("The holding period must be between 1 and 10 days!");
        return None;
    
    if (business_days > 253 or business_days < 250):
        print("The business days number must be between 250 and 253!");
        return None;
    
    if (confidence_level > 1 or confidence_level <= 0):
        print("The confidence level must be less than 1 and more than 0!");
        return None;
    #################### End of input checks: ####################

    # Loads the data from the csv file into a DataFrame:
    dtype_dict = { # dictates how the data will be interpreted
    'Open': 'float',
    'High': 'float',
    'Low': 'float',
    'Close': 'float',
    'Adj. close': 'float'
    };
    price_data = PD.read_csv(input_file, header=0, index_col=0, parse_dates=True, dtype=dtype_dict, thousands=',');
    
    # Making sure there is enough data to work with:
    if (lookback_period*business_days > price_data['Adj. close'].size):
        print("Not enough data points to calculate %d-year VaR!" % (lookback_period));
        return None;
    else:
        price_data = price_data.head(lookback_period*business_days); # only keeps data within the look-back period
    
    # Creates a new column for log returns and populates it with the 1-day log returns:
    price_data['Log return'] = NP.log(price_data['Adj. close'] / price_data['Adj. close'].shift(-1));
    
    # If holding period longer than 1 day, calculate their log returns and replace in the 'Log return' column if lower:
    if (holding_period > 1):
        for i in range(2, holding_period+1):
            price_data['temp log return'] = NP.log(price_data['Adj. close'] / price_data['Adj. close'].shift(-i));
            price_data['Log return'] = price_data[['Log return', 'temp log return']].min(axis=1);
            price_data.drop('temp log return', axis=1);
    
    price_data.dropna(); # removes any rows with NaN
    
    VaR = -price_data['Log return'].quantile(1-confidence_level, interpolation='nearest');
    ES = -NP.average(price_data['Log return'][price_data['Log return'] < price_data['Log return'].quantile(1-confidence_level)]);
    volatility = price_data['Log return'].std()*math.sqrt(lookback_period); # annualised volatility
    
    price_data['Log return'].plot(figsize=(12,6), ls="-", color="blue")
    
    return {
        "VaR": round(VaR,4),
        "Expected shortfall": round(ES,4),
        "Volatility": round(volatility,4)
    };