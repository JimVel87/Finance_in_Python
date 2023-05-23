import math;
from scipy.optimize import fsolve;

def phi(x):
    # Cumulative distribution function for the standard normal distribution
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0;
    # Note: erf(z) is the integral of the normal distribution from 0 to z scaled such that erf(+inf) = +1 and erf(-inf) = -1

class Forward:
    def __init__(self, forward_price, time_to_expiry):
        self.forward_price = forward_price;
        self.time_to_expiry = time_to_expiry;
    def payoff(self, market_price, position_size=1):
        return (market_price - self.forward_price) * position_size;
    def value(self, market_price, discount_rate, position_size=1):
        return (market_price - self.forward_price*math.e**(-discount_rate*self.time_to_expiry)) * position_size;
    def delta(self, dividend_yield=0, position_size=1):
        return math.e**(-dividend_yield*self.time_to_expiry) * position_size;

class Future(Forward):
    def __init__(self, forward_price, time_to_expiry, lot_size):
        super().__init__(forward_price, time_to_expiry);
        self.lot_size = lot_size;
    def payoff(self, market_price, position_size=1):
        return (market_price - self.forward_price) * self.lot_size * position_size;
    def value(self, market_price, discount_rate, position_size=1):
        return (market_price - self.forward_price*math.e**(-discount_rate*self.time_to_expiry)) * self.lot_size * position_size;
    def delta(self, discount_rate, dividend_yield=0, position_size=1):
        return math.e**((discount_rate-dividend_yield)*self.time_to_expiry) * position_size;

class Option:
    def __init__(self, option_type, option_style, strike_price, time_to_expiry):
        option_types = ['call', 'put'];
        if option_type not in option_types:
            raise ValueError("Invalid option type. Expected one of: %s" % option_types);
        option_styles = ['European', 'American'];
        if option_style not in option_styles:
            raise ValueError("Invalid option style. Expected one of: %s" % option_styles);
        self.option_type = option_type;
        self.option_style = option_style;
        self.strike_price = strike_price;
        self.time_to_expiry = time_to_expiry; # in years
    def payoff(self, underlying_price, position_size=1):
        if self.option_type == 'call':
            return (underlying_price - self.strike_price) * position_size if underlying_price > self.strike_price else 0;
        else:
            return (self.strike_price - underlying_price) * position_size if underlying_price < self.strike_price else 0;

def Binomial_price(option, steps, up_value_change, down_value_change, discount_rate, initial_underlying_price, dividend_yield):
    """
    Calculation of an option's price in simulated lattice (discrete time).
    'option': an option-class object
    'steps': the number of time steps to simulate
    'value_change': the increase or decrease in the value of the underlying in each time step as a factor to its initial value
    'discount_rate': the annualised rate at which future values are discounted
    'initial_underlying_price': the price of the underlying at t=0
    'dividend_yield': the rate at which the underlying pays dividends; set to 0 to ignore. For foreign currency, treat it as the
        foreign risk-free interest rate.
    It creates the underlying's price states of the last step in the binomial tree and calculates the option's expected payoff.
    Then performs a backwards induction by discounting the option's value to calculate the option's price at t=0.
    """
    if isinstance(option, Option) == False:
        print("Function 'Binomial_price' can only be used to price options!");
        return None;
    
    step_size = option.time_to_expiry/steps;
    # The risk-neutral probability of an up move is p=(e^((r-q)T)-d)/(u-d):
    up_probability = (math.e**((discount_rate-dividend_yield)*step_size)-down_value_change)/(up_value_change - down_value_change);
    expected_option_value = 0;
    
    #################### Calculation for European options ####################
    # Note: number of nodes = number of states x number of combinations for each state (for example ud and du is one state with two combinations)
    if option.option_style == 'European':
        for i in range(steps+1): # there are step+1 different final states in the tree
            # Price determined by the number of up and down movements:
            underlying_price = initial_underlying_price * up_value_change**(steps-i) * down_value_change**i;
            # There are n!/r!(n-r)! u and d combinations for each different state, where n is the step number and r the number of up movements:
            number_of_states = math.factorial(steps)/(math.factorial(steps-i)*math.factorial(i));
            # Note on the above: the second factor in the denominator would be: factorial(steps-r) but the number of up movements is given...
            # ...by steps-i in the loop, thus: factorial(steps-r) = factorial(steps - steps + i) = factorial(i).
            expected_option_value += number_of_states * up_probability**(steps-i) * (1-up_probability)**i * option.payoff(underlying_price,1);
            # Note on payoff(): for the purposes of this simulation we assume contract size of 1
        return expected_option_value * math.e**(-discount_rate*option.time_to_expiry); # the discounted option value
    
    #################### Calculation for American options ####################
    else:
        # It creates a list of lists, the master list will end up having size = sum(n^r) for all steps (n=2, r=1,2,... until the last step):
        tree = [[initial_underlying_price,None]]; # a list of all nodes in sublist form, element 0 is the underlying price...
                                                # ...and element 1 is the option value (initialised with 'None')
        for i in range(0,steps): # runs for every step
            for j in range(2**i): # each step doubles the count of nodes
                tree.append([tree[2**i-1+j][0]*up_value_change,None]);
                tree.append([tree[2**i-1+j][0]*down_value_change,None]);
                # Note: nodes with the same underling price are NOT merged!
        # Below it calculates the option's payoff for the final nodes only:
        for j in range(1,2**steps+1): # there are 2^steps final nodes
            tree[-j][1] = option.payoff(tree[-j][0],1);
        # For all non-final nodes, it calculates the option value as the maximum of its intrinsic value and the discounted...
        # ...probability-weighted value in the two subsequent nodes (variable 'dpwv' below):
        for i in range(steps-1,-1,-1): # runs for every step (reverse from step-1 to 0)
            for j in range(2**i):
                dpwv = (tree[2**(i+1)+2*j-1][1]*up_probability+tree[2**(i+1)+2*j][1]*(1-up_probability))*math.e**(-discount_rate*step_size);
                tree[2**i-1+j][1] = max(option.payoff(tree[2**i-1+j][0],1), dpwv);
                # Note on payoff(): for the purposes of this simulation we assume contract size of 1
        return round(tree[0][1],4);

def Binomial_price_with_volatility(option, steps, volatility, discount_rate, initial_underlying_price, dividend_yield):
    """
    Calculation of an option's price in simulated lattice (discrete time).
    'option': an option-class object
    'steps': the number of time steps to simulate
    'volatility': informs the up and down price movements of the underlying
    'discount_rate': the annualised rate at which future values are discounted
    'initial_underlying_price': the price of the underlying at t=0
    'dividend_yield': the rate at which the underlying pays dividends; set to 0 to ignore. For foreign currency, treat it as the
        foreign risk-free interest rate.
    It creates the underlying's price states of the last step in the binomial tree and calculates the option's expected payoff.
    Then performs a backwards induction by discounting the option's value to calculate the option's price at t=0.
    """
    if isinstance(option, Option) == False:
        print("Function 'Binomial_price_with_volatility' can only be used to price options!");
        return None;
    
    step_size = option.time_to_expiry/steps;
    up_value_change = math.e**(volatility*math.sqrt(step_size));
    down_value_change = math.e**(-volatility*math.sqrt(step_size));
    # The risk-neutral probability of an up move is p=(e^((r-q)T)-d)/(u-d):
    up_probability = (math.e**((discount_rate-dividend_yield)*step_size)-down_value_change)/(up_value_change - down_value_change);
    expected_option_value = 0;
    
    #################### Calculation for European options ####################
    # Note: number of nodes = number of states x number of combinations for each state (for example ud and du is one state with two combinations)
    if option.option_style == 'European':
        for i in range(steps+1): # there are step+1 different final states in the tree
            # Price determined by the number of up and down movements:
            underlying_price = initial_underlying_price * up_value_change**(steps-i) * down_value_change**i;
            # There are n!/r!(n-r)! u and d combinations for each different state, where n is the step number and r the number of up movements:
            number_of_states = math.factorial(steps)/(math.factorial(steps-i)*math.factorial(i));
            # Note on the above: the second factor in the denominator would be: factorial(steps-r) but the number of up movements is given...
            # ...by steps-i in the loop, thus: factorial(steps-r) = factorial(steps - steps + i) = factorial(i).
            expected_option_value += number_of_states * up_probability**(steps-i) * (1-up_probability)**i * option.payoff(underlying_price,1);
            # Note on payoff(): for the purposes of this simulation we assume contract size of 1
        return expected_option_value * math.e**(-discount_rate*option.time_to_expiry); # the discounted option value
    
    #################### Calculation for American options ####################
    else:
        # It creates a list of lists, the master list will end up having size = sum(n^r) for all steps (n=2, r=1,2,... until the last step):
        tree = [[initial_underlying_price,None]]; # a list of all nodes in sublist form, element 0 is the underlying price...
                                                # ...and element 1 is the option value (initialised with 'None')
        for i in range(0,steps): # runs for every step
            for j in range(2**i): # each step doubles the count of nodes
                tree.append([tree[2**i-1+j][0]*up_value_change,None]);
                tree.append([tree[2**i-1+j][0]*down_value_change,None]);
                # Note: nodes with the same underling price are NOT merged!
        # Below it calculates the option's payoff for the final nodes only:
        for j in range(1,2**steps+1): # there are 2^steps final nodes
            tree[-j][1] = option.payoff(tree[-j][0],1);
        # For all non-final nodes, it calculates the option value as the maximum of its intrinsic value and the discounted...
        # ...probability-weighted value in the two subsequent nodes (variable 'dpwv' below):
        for i in range(steps-1,-1,-1): # runs for every step (reverse from step-1 to 0)
            for j in range(2**i):
                dpwv = (tree[2**(i+1)+2*j-1][1]*up_probability+tree[2**(i+1)+2*j][1]*(1-up_probability))*math.e**(-discount_rate*step_size);
                tree[2**i-1+j][1] = max(option.payoff(tree[2**i-1+j][0],1), dpwv);
                # Note on payoff(): for the purposes of this simulation we assume contract size of 1
        return round(tree[0][1],4);

def BSM_price(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield):
    """
    Analytical (closed-form) calculation of an option's price in continuous time:
    c = S0e^(-qT)N(d1)-Ke^(-rT)N(d2), p = Ke^(-rT)N(-d2)-S0e^(-qT)N(-d1) where:
    d1 = [ln(S0/K)+(r-q+σ^2/2)T]/σ*sqrt(T) and d2 = d1 - σ*sqrt(T)
    S0: underlying price, K: strike price, r: risk-free interest rate, T: time to expiry, σ: volatility, q: dividend yield,
    N(): cumulative standard normal distribution
    """    
    if isinstance(option, Option) == False:
        print("Function 'BSM_price' can only be used to price options!");
        return None;

    # short variable names for readability
    S0 = underlying_price;
    Rf = risk_free_interest_rate;
    sigma = volatility;
    q = dividend_yield;
    K = option.strike_price;
    T = option.time_to_expiry;

    # Check option style; BSM is only for European options:
    if option.option_style == 'American':
        print("The Black-Scholes model is only used to price European-style options, as it does not take into account that American-style options could be exercised before the expiration date!");
        return None;
    else:
        d1 = (math.log(S0/K, math.e) + (Rf-q+sigma**2/2)*T) / (sigma*math.sqrt(T));
        d2 = d1 - sigma*math.sqrt(T);
        if option.option_type == 'call':
            return round(S0*math.e**(-q*T)*phi(d1) - K*math.e**(-Rf*T)*phi(d2),4);
        else:
            return round(K*math.e**(-Rf*T)*phi(-d2) - S0*math.e**(-q*T)*phi(-d1),4);

def BSM_warrant_price(warrant, underlying_price, risk_free_interest_rate, volatility, outstanding_shares, number_of_warrants, dividend_yield):
    """
    Variation of BSM model for options to price warrants. Warrants are modeled as options.
    """
    if isinstance(warrant, Option) == False:
        print("Function 'BSM_warrant_price' can only be used to price warrants!");
        return None;

    # short variable names for readability
    S0 = underlying_price;
    Rf = risk_free_interest_rate;
    sigma = volatility;
    q = dividend_yield;
    K = warrant.strike_price;
    T = warrant.time_to_expiry;

    # Check warrant style; BSM is only for European warrants:
    if warrant.option_style == 'American':
        print("The Black-Scholes model is only used to price European-style warrants, as it does not take into account that American-style warrants could be exercised before the expiration date!");
        return None;
    else:
        haircut = outstanding_shares / (outstanding_shares + number_of_warrants); # multiplier to account for dilution
        d1 = (math.log(S0/K, math.e) + (Rf-q+sigma**2/2)*T) / (sigma*math.sqrt(T));
        d2 = d1 - sigma*math.sqrt(T);
        if warrant.option_type == 'call':
            return round((S0*math.e**(-q*T)*phi(d1) - K*math.e**(-Rf*T)*phi(d2))*haircut,4);
        else:
            return round((K*math.e**(-Rf*T)*phi(-d2) - S0*math.e**(-q*T)*phi(-d1))*haircut,4);

def BSM_for_fsolve(volatility, option_price, option, underlying_price, risk_free_interest_rate, dividend_yield):
    """
    This function is only called by BSM_implied_volatility().
    It simply realigns the arguments and the result calculation so that it works with scipy.optimize.fsolve() root finder.
    """
    return option_price - BSM_price(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield);

def BSM_implied_volatility(option, option_price, underlying_price, risk_free_interest_rate, dividend_yield):
    """
    Given an option, its observed price and all other parameters, it goal-seeks the implied volatility.
    fsolve() returns the result in array format; [0] is used to convert the return value to scalar.
    Starting estimate set to 10%.
    """
    return fsolve(BSM_for_fsolve, 0.1, args=(option_price, option, underlying_price, risk_free_interest_rate, dividend_yield))[0];

def BSM_delta(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield):
    if (option.option_style == 'American'):
        print("Function 'BSM_delta' only works with European-style options!");
        return None;

    # short variable names for readability
    S0 = underlying_price;
    Rf = risk_free_interest_rate;
    sigma = volatility;
    q = dividend_yield;
    K = option.strike_price;
    T = option.time_to_expiry;

    d1 = (math.log(S0/K, math.e) + (Rf-q+sigma**2/2)*T) / (sigma*math.sqrt(T));
    if option.option_type == 'call':
        return round(math.e**(-q*T)*phi(d1),4);
    else:
        return round(math.e**(-q*T)*(phi(d1)-1),4);

def BSM_gamma(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield):
    if (option.option_style == 'American'):
        print("Function 'BSM_gamma' only works with European-style options!");
        return None;

    # short variable names for readability
    S0 = underlying_price;
    Rf = risk_free_interest_rate;
    sigma = volatility;
    q = dividend_yield;
    K = option.strike_price;
    T = option.time_to_expiry;

    d1 = (math.log(S0/K, math.e) + (Rf-q+sigma**2/2)*T) / (sigma*math.sqrt(T));
    return round((math.e**(-d1**2/2)/math.sqrt(2*math.pi)) / (S0*sigma*math.sqrt(T)),4);

def BSM_vega(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield):
    if (option.option_style == 'American'):
        print("Function 'BSM_vega' only works with European-style options!");
        return None;

    # short variable names for readability
    S0 = underlying_price;
    Rf = risk_free_interest_rate;
    sigma = volatility;
    q = dividend_yield;
    K = option.strike_price;
    T = option.time_to_expiry;

    d1 = (math.log(S0/K, math.e) + (Rf-q+sigma**2/2)*T) / (sigma*math.sqrt(T));
    return round(S0*math.sqrt(T)*math.e**(-d1**2/2) / math.sqrt(2*math.pi),4);

def BSM_theta(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield):
    """
    Note: the theta calculated by this function is the annual amount. To get the daily theta you need to divide by 365.
    """
    if (option.option_style == 'American'):
        print("Function 'BSM_vega' only works with European-style options!");
        return None;

    # short variable names for readability
    S0 = underlying_price;
    Rf = risk_free_interest_rate;
    sigma = volatility;
    q = dividend_yield;
    K = option.strike_price;
    T = option.time_to_expiry;

    d1 = (math.log(S0/K, math.e) + (Rf-q+sigma**2/2)*T) / (sigma*math.sqrt(T));
    d2 = d1 - sigma*math.sqrt(T);
    part_1 = (-S0*math.e**(-d1**2/2)/math.sqrt(2*math.pi)*sigma) / (2*math.sqrt(T));
    if option.option_type == 'call':
        return round(part_1 - Rf*K*math.e**(-Rf*T)*phi(d2),4);
    else:
        return round(part_1 + Rf*K*math.e**(-Rf*T)*phi(-d2),4);

def BSM_rho(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield):
    if (option.option_style == 'American'):
        print("Function 'BSM_vega' only works with European-style options!");
        return None;

    # short variable names for readability
    S0 = underlying_price;
    Rf = risk_free_interest_rate;
    sigma = volatility;
    q = dividend_yield;
    K = option.strike_price;
    T = option.time_to_expiry;

    d1 = (math.log(S0/K, math.e) + (Rf-q+sigma**2/2)*T) / (sigma*math.sqrt(T));
    d2 = d1 - sigma*math.sqrt(T);
    if option.option_type == 'call':
        return round(K*T*math.e**(-Rf*T)*phi(d2),4);
    else:
        return round(-K*T*math.e**(-Rf*T)*phi(-d2),4);

def Option_Stats(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield):
    if (option.option_style == 'American'):
        print("Function 'Option_Stats' uses the Black-Scholes model, which only works with European-style options!");
        return None;
    else:
        return {
            "Option type": option.option_type,
            "Option style": option.option_style,
            "Strike price": option.strike_price,
            "Expiry in years": option.time_to_expiry,
            "Option value": BSM_price(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield),
            "Delta": BSM_delta(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield),
            "Gamma": BSM_gamma(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield),
            "Vega": BSM_vega(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield),
            "Theta": BSM_theta(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield),
            "Rho": BSM_rho(option, underlying_price, risk_free_interest_rate, volatility, dividend_yield)
        };