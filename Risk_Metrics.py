import pandas as PD;
import numpy as NP;
import math;
import scipy.stats;
import matplotlib.pyplot as plt;

def Stats_on_csv(input_file, lookback_period, holding_period, confidence_level, business_days=252, save_file=True):
    """
    It calculates Value-at-Risk at the given confidence level for given look-back and holding periods.
    Look-back period is in years and holding_period is in days. It assumes 252 business days in a year.
    The input file is in csv format retrieved from Yahoo! Finance. Column format:
    Date | Open | High | Low | Close | Adj. close | Volume
    VaR is given in % calculated on the worst log returns in the holding period.
    If save_file is true, it saves a copy of the data frame as csv file.
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
    
    # Cleanup:
    price_data.dropna(); # removes any rows with NaN
    price_data.drop('temp log return');
    
    VaR = -price_data['Log return'].quantile(1-confidence_level, interpolation='nearest');
    ES = -NP.average(price_data['Log return'][price_data['Log return'] < price_data['Log return'].quantile(1-confidence_level)]);
    volatility = price_data['Log return'].std()*math.sqrt(lookback_period); # annualised volatility
    # Volatility above is calculated with the simple variance method, thus all observations have the same weight.
    
    # Visualisation:
    price_data['Log return'].plot(figsize=(12,6), ls="-", color="blue", label="Daily log returns", legend=True);
    plt.hlines(y=-VaR, xmin=price_data.index[0], xmax=price_data.index[len(price_data.index)-1], color='r', linestyle='-', label='VaR');
    plt.legend();

    if save_file:
        price_data.to_csv('log_returns_' + input_file);
    
    return {
        "VaR": round(VaR,4),
        "Expected shortfall": round(ES,4),
        "Volatility": round(volatility,4)
    };

def Binomial_VaR_backtesting(input_file, VaR, VaR_level, confidence_level):
    """
    It performs dirty backtesting on a VaR model. It assumes overshoots are independent and follow the binomial distribution.
    The input file is in csv format retrieved from Yahoo! Finance, after log returns have been calculated. Column format:
    Date | Open | High | Low | Close | Adj. close | Volume | Log return
    """
    #################### Input checks: ####################
    if (type(input_file) != str):
        print("The input file name must be a string!");
        return None;

    if (VaR > 1 or VaR <= 0):
        print("VaR must be less than 1 and more than 0!");
        return None;
    
    if (VaR_level > 1 or VaR_level <= 0):
        print("The VaR level must be less than 1 and more than 0!");
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
    'Adj. close': 'float',
    'Log return': 'float'
    };
    return_history = PD.read_csv(input_file, header=0, index_col=0, parse_dates=True, dtype=dtype_dict, thousands=',');

    observations = len(return_history['Log return']); # number of total observations
    overshoots = len(return_history.loc[return_history['Log return']<-VaR]); # number of observations where the log return was exceeding VaR
    overshoot_probability = 1 - VaR_level;
    # Normal approximation to binomial distribution:
    expected_overshoots = observations * overshoot_probability;
    standard_deviation = math.sqrt(observations * overshoot_probability * (1-overshoot_probability));
    # The approximation follows the standard normal distribution:
    z_statistic = (overshoots - expected_overshoots) / standard_deviation;
    # The null hypothesis is that the model is correct. Obtain the non-rejection region:
    significance = 1 - confidence_level;
    upper_value = scipy.stats.norm.ppf(1-significance/2);
    lower_value = -upper_value;

    # Results:
    if z_statistic > lower_value and z_statistic < upper_value:
        print("Cannot reject the hypothesis that the model is correct at %.4f confidence level" % (confidence_level));
    else:
        print("Reject the hypothesis that the model is correct at %.4f confidence level" % (confidence_level));
    
    return {
        "Observations": observations,
        "Overshoots": overshoots,
        "Z-statistic": round(z_statistic,4),
        "Non-rejection region": [round(lower_value,4),round(upper_value,4)]
    };
