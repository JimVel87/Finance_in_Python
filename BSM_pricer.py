import tkinter as TK; # for the GUI
import Products_and_Pricing as PaP; # for the option class and pricing functions

def is_float(string): # function to check if input is a number (int or float)
    try:
        float(string); # try converting the string to float
        return True; # if successful, return true
    except ValueError:
        return False; # otherwise, return false

def price_calc_selected(): # if the user chooses to calculate for price
    price_value.delete(0, 'end'); # the field to give a price is cleared (delete characters from start to end)
    price_value.config(state='disabled'); # the field to give a price is disabled
    volatility_value.config(state='normal'); # the field to give volatility is enabled

def vol_calc_selected(): # if the user chooses to calculate for volatility
    price_value.config(state='normal'); # the field to give a price is enabled
    volatility_value.delete(0, 'end'); # the field to give volatility is cleared (delete characters from start to end)
    volatility_value.config(state='disabled'); # the field to give volatility is disabled

# The window
root = TK.Tk(); # creates the root (main) window
root.title("BSM option pricer");
root.geometry("460x300"); # the window dimensions

# Constants for widget alignment
COL1 = 20;
COL2 = 130;
COL3 = 260;
COL4 = 360;
ROW1 = 20;
ROW2 = 40;
ROW3 = 80;
ROW4 = 100;
ROW5 = 120;
ROW6 = 140;
ROW7 = 160;
ROW8 = 200;

# The radio buttons for the option type with their labels
option_type = TK.StringVar(value='call'); # the variable controlled by the option type radio buttons
# the variable is initialised, otherwise both radio buttons would start as selected
RB_call = TK.Radiobutton(root, text='Call', variable=option_type, value='call');
RB_call.place(x=COL1, y=ROW1);
RB_put = TK.Radiobutton(root, text='Put', variable=option_type, value='put');
RB_put.place(x=COL1, y=ROW2);

# The radio buttons for the calculation type (price or volatility)
calc_type = TK.StringVar(value='price');
calc_price = TK.Radiobutton(root, text='Calculate price', variable=calc_type, value='price', command=price_calc_selected);
calc_price.place(x=COL3, y=ROW1);
calc_vol = TK.Radiobutton(root, text='Calculate volatility', variable=calc_type, value='vol', command=vol_calc_selected);
calc_vol.place(x=COL3, y=ROW2);

# The labels for the input info
strike_price_label = TK.Label(root, text='Strike price:');
strike_price_label.place(x=COL1, y=ROW3);
strike_price_value = TK.Entry(root, width=10);
strike_price_value.place(x=COL2, y=ROW3);
underlying_price_label = TK.Label(root, text='Underlying price:');
underlying_price_label.place(x=COL1, y=ROW4);
underlying_price_value = TK.Entry(root, width=10);
underlying_price_value.place(x=COL2, y=ROW4);
expiry_label = TK.Label(root, text='Expiry in years:');
expiry_label.place(x=COL1, y=ROW5);
expiry_value = TK.Entry(root, width=10);
expiry_value.place(x=COL2, y=ROW5);
risk_free_rate_label = TK.Label(root, text='Risk-free rate:');
risk_free_rate_label.place(x=COL1, y=ROW6);
risk_free_rate_value = TK.Entry(root, width=10);
risk_free_rate_value.place(x=COL2, y=ROW6);
dividend_yield_label = TK.Label(root, text='Dividend yield:');
dividend_yield_label.place(x=COL1, y=ROW7);
dividend_yield_value = TK.Entry(root, width=10);
dividend_yield_value.place(x=COL2, y=ROW7);

# The price / volatility labels
price_label = TK.Label(root, text='Option price:');
price_label.place(x=COL1, y=ROW8);
price_value = TK.Entry(root, width=10, state='disabled');
price_value.place(x=COL2, y=ROW8);
volatility_label = TK.Label(root, text='Volatility:');
volatility_label.place(x=COL3, y=ROW8);
volatility_value = TK.Entry(root, width=10);
volatility_value.place(x=COL4, y=ROW8);

# The labels for the results
delta_label = TK.Label(root, text='Delta:');
delta_label.place(x=COL3, y=ROW3);
delta_result = TK.Label(root, text='0');
delta_result.place(x=COL4, y=ROW3);
gamma_label = TK.Label(root, text='Gamma:');
gamma_label.place(x=COL3, y=ROW4);
gamma_result = TK.Label(root, text='0');
gamma_result.place(x=COL4, y=ROW4);
vega_label = TK.Label(root, text='Vega:');
vega_label.place(x=COL3, y=ROW5);
vega_result = TK.Label(root, text='0');
vega_result.place(x=COL4, y=ROW5);
theta_label = TK.Label(root, text='Theta:');
theta_label.place(x=COL3, y=ROW6);
theta_result = TK.Label(root, text='0');
theta_result.place(x=COL4, y=ROW6);
rho_label = TK.Label(root, text='Rho:');
rho_label.place(x=COL3, y=ROW7);
rho_result = TK.Label(root, text='0');
rho_result.place(x=COL4, y=ROW7);

# Bottom label for error messages
err_msg = TK.Label(root);
err_msg.place(x=200, y=280);

# A function to check the input values - it is called by option_calc()
def input_check():
    if calc_type.get() == 'price': # if calculating price...
        if not is_float(volatility_value.get()): # volatility must be a number
            err_msg.config(text = 'All inputs must be numbers!');
            return None;
    else: # if calculating volatility...
        if not is_float(price_value.get()): # price must be a number
            err_msg.config(text = 'All inputs must be numbers!');
            return None;
    # then check the other input values
    if not is_float(strike_price_value.get()) or not is_float(underlying_price_value.get()) or not is_float(expiry_value.get()) or \
                            not is_float(risk_free_rate_value.get()) or not is_float(dividend_yield_value.get()):
        err_msg.config(text = 'All inputs must be numbers!');
        return None;
    err_msg.config(text=''); # clear any error messages
    return 1; # all input values are numbers

# The calculation function
def option_calc():
    if input_check() == 1: # if all input checks passed...
        # first create the variables:
        strike_price = float(strike_price_value.get());
        time_to_expiry = float(expiry_value.get());
        underlying_price = float(underlying_price_value.get());
        risk_free_rate = float(risk_free_rate_value.get());
        dividend_yield = float(dividend_yield_value.get());
        # then create the option object:
        the_option = PaP.Option(option_type.get(), 'European', strike_price, time_to_expiry);
        if calc_type.get() == 'price': # if calculating price...
            volatility = float(volatility_value.get());
            price_value.config(state='normal'); # activate the entry field to insert the option price
            price_value.delete(0, 'end'); # clear any existing value in it
            price_value.insert(0, PaP.BSM_price(the_option, underlying_price, risk_free_rate, volatility, dividend_yield));
            price_value.config(state='disabled'); # now deactivate the entry field
        else: # if calculating volatility...
            option_price = float(price_value.get());
            volatility_value.config(state='normal'); # activate the entry field to insert the volatility value
            volatility_value.delete(0, 'end'); # clear any existing value in it
            volatility = PaP.BSM_implied_volatility(the_option, option_price, underlying_price, risk_free_rate, dividend_yield);
            volatility_value.insert(0, volatility);
            volatility_value.config(state='disabled'); # now deactivate the entry field
        # finally calculate the greeks:
        delta_result.config(text=PaP.BSM_delta(the_option, underlying_price, risk_free_rate, volatility, dividend_yield));
        gamma_result.config(text=PaP.BSM_gamma(the_option, underlying_price, risk_free_rate, volatility, dividend_yield));
        vega_result.config(text=PaP.BSM_vega(the_option, underlying_price, risk_free_rate, volatility, dividend_yield));
        theta_result.config(text=PaP.BSM_theta(the_option, underlying_price, risk_free_rate, volatility, dividend_yield));
        rho_result.config(text=PaP.BSM_rho(the_option, underlying_price, risk_free_rate, volatility, dividend_yield));
    else: # if checks not passed:
        return None # do not calculate anything; input_check() will handle the error message

# The button
calc_button = TK.Button(root, text='Calculate', command=option_calc); # creates a button that calls the calculation function
calc_button.place(x=200, y=240);

root.update_idletasks();
root.mainloop();