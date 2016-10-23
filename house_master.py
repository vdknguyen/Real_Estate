
import pandas as pd
import numpy as np

class House():

    # Static Class Variables
    #yearly_house_appreciation = .02
    #marginal_tax_rate = .25 
    #expected_deduction = 6400 # expected standard deduction for current year
    #expected_deduction_yearly_increase = 100 # expected increase in standard deduction each year
    #property_tax = .01 # percent of house value payed as yearly property tax
    #long_term_capital_gains = .15
    #yearly_maintenance = .003 # percent of house value set aside yearly for repairs and maintenance
    #hoa_yearly_increase = .01 # yearly percent increase in hoa fee
    #homeowner_yearly_increase = .01 # yearly percent increase in insurance
    #closing_buy = .06 # percent of house value for closing cost when buying
    #closing_sell = .06 # percent of house value for closing cost when selling
    #rent_yearly_increase= .01 # yearly percent increase in rent
    #percent_vacancy = 1.0/12.0 # percent of the year with vacancy
    #investment_return = .07 #average yearly return

    def __init__(self, inputs):
        self.inputs = inputs

    
    def amortization(self,n,interest,marginal_tax_rate,price,offer,down_payment,yearly_house_appreciation):
        L = offer * (1.0 - down_payment) # loan amount
        monthly_interest = interest/12.0 # monthly interest rate as a percent/100
        I = monthly_interest
        numerator = L*(1 + I)**n
        denomenator = -1*(1 - (1 + I)**n) / I
        p = numerator/denomenator # monthly payment
        # Amortization
        mortgage = pd.DataFrame()
        loan = L
        month_list = range(1,n+1)
        for month in month_list: # simulate monthly payment
            mortgage_month = pd.DataFrame()
            mortgage_month['Month'] = [month]
            mortgage_month['Loan_Before_Payment'] = loan
            loan = loan * (1+ monthly_interest) - p
            mortgage_month['Loan_After_Payment'] = loan
            mortgage_month['Equity_Gain'] = mortgage_month['Loan_Before_Payment'] - mortgage_month['Loan_After_Payment']
            mortgage = pd.concat([mortgage,mortgage_month])
        mortgage['Interest_Paid'] = p - mortgage['Equity_Gain']
        mortgage['Tax_Savings'] = mortgage['Interest_Paid'] * marginal_tax_rate
        mortgage['Cumulative_Tax_Savings'] = mortgage['Tax_Savings'].cumsum()
        mortgage['Year'] = np.ceil(mortgage['Month']/12.0)
        mortgage['Cumulative_Equity_Gain'] = mortgage['Equity_Gain'].cumsum()
        mortgage['Cumulative_Interest_Paid'] = mortgage['Interest_Paid'].cumsum()
        mortgage['Total_Equity_With_Appreciation'] = (mortgage['Cumulative_Equity_Gain']*(price/offer) + down_payment * price) * (1 + yearly_house_appreciation)**mortgage['Year']
        mortgage.set_index([range(len(mortgage))], inplace = True)
        return mortgage,p

    def calculate_cost(self,inputs):

        time = inputs['time']
        interest = inputs['interest']
        price = inputs['initial_value']
        offer = inputs['offer']
        down_payment = inputs['down_payment']
        yearly_house_appreciation = inputs['yearly_house_appreciation']

        # Taxes
        marginal_tax_rate = inputs['marginal_tax_rate'] 
        expected_deduction = inputs['expected_deduction']
        expected_deduction_yearly_increase = inputs['expected_deduction_yearly_increase']
        property_tax = inputs['property_tax']
        long_term_capital_gains = inputs['long_term_capital_gains']

        # Extra Costs
        yearly_maintenance = inputs['yearly_maintenance']
        hoa_fee = inputs['hoa_fee']
        hoa_yearly_increase = inputs['hoa_yearly_increase']
        homeowner_insurance = inputs['homeowner_insurance']
        homeowner_yearly_increase = inputs['homeowner_yearly_increase']
        closing_buy = inputs['closing_buy']
        closing_sell = inputs['closing_sell']

        #Rental Income
        monthly_rent = inputs['monthly_rent']
        rent_yearly_increase = inputs['rent_yearly_increase']
        percent_vacancy = inputs['percent_vacancy']
        rent_percent = inputs['rent_percent']

        # Oportunity costs
        investment_return = inputs['investment_return']
        opportunity_rent = inputs['opportunity_rent']

        # Amortization
        n = time * 12 #number of months for the loan
        mortgage,p = self.amortization(n,interest,marginal_tax_rate,price,offer,down_payment,yearly_house_appreciation)
    

        # Yearly Info:

        yearly_mortgage = mortgage[mortgage.Month%12 == 0] # Gives end of the year
        yearly_mortgage = yearly_mortgage[['Year','Cumulative_Interest_Paid','Total_Equity_With_Appreciation','Cumulative_Tax_Savings']]

        # House Appreciation
        yearly_mortgage['House_Value'] = price * (1 + yearly_house_appreciation)**yearly_mortgage['Year']

        # Taxes
        yearly_mortgage['Property_Tax'] = property_tax * yearly_mortgage['House_Value']
        yearly_mortgage['Cumulative_Property_Tax'] = yearly_mortgage['Property_Tax'].cumsum()
        yearly_mortgage['Tax_Savings'] = yearly_mortgage['Cumulative_Tax_Savings']
        yearly_mortgage['Tax_Savings'].iloc[1:len(yearly_mortgage)] = np.diff(yearly_mortgage['Cumulative_Tax_Savings']) # Yearly tax deduction from interest
        yearly_mortgage['Tax_Savings'] += marginal_tax_rate * yearly_mortgage['Property_Tax'] # yearly tax deduction from property tax
        yearly_mortgage['Expected_Tax_Savings'] = (expected_deduction + expected_deduction_yearly_increase * mortgage['Year']) * (marginal_tax_rate) # Tax savings from standard dedecution
        yearly_mortgage['Effective_Tax_Savings'] = yearly_mortgage['Tax_Savings'] - yearly_mortgage['Expected_Tax_Savings'] # Difference between interest+property tax deduction and standard deduction
        yearly_mortgage['Effective_Tax_Savings'] = yearly_mortgage['Effective_Tax_Savings'].apply(lambda x: x if x > 0 else 0) # Only count if savings above what you would get from standard deduction
        yearly_mortgage['Cumulative_Tax_Savings'] = yearly_mortgage['Effective_Tax_Savings'].cumsum()

        # Total Costs
        yearly_mortgage['HOA'] = 12 * hoa_fee * ((1 + hoa_yearly_increase) ** yearly_mortgage['Year'])
        yearly_mortgage['Cumulative_HOA'] = yearly_mortgage['HOA'].cumsum()
        yearly_mortgage['Homeowner_Insurance'] = 12 *homeowner_insurance * ((1 + homeowner_yearly_increase) ** yearly_mortgage['Year'])
        yearly_mortgage['Cumulative_Homeowner_Insurance'] = yearly_mortgage['Homeowner_Insurance'].cumsum()
        yearly_mortgage['Maintenance'] = yearly_maintenance * yearly_mortgage['House_Value']
        yearly_mortgage['Cumulative_Maintenance'] = yearly_mortgage['Maintenance'].cumsum()
        yearly_mortgage['Total_Cost'] = yearly_mortgage['Cumulative_Property_Tax'] + yearly_mortgage['Cumulative_Interest_Paid']+ yearly_mortgage['Cumulative_HOA']+ yearly_mortgage['Cumulative_Homeowner_Insurance']+ yearly_mortgage['Cumulative_Maintenance'] + offer * closing_buy + yearly_mortgage['House_Value'] * closing_sell

        # Rental income
        yearly_mortgage['Rent_Income'] = ((1-marginal_tax_rate) * (1 - percent_vacancy) * 12 * monthly_rent * rent_percent ) * ((1 + rent_yearly_increase) ** yearly_mortgage['Year']) # Rent is taxed as income
        yearly_mortgage['Cumulative_Rent_Income'] = yearly_mortgage['Rent_Income'].cumsum()

        # Summary
        yearly_mortgage['Effective_Cost'] = yearly_mortgage['Total_Cost'] - yearly_mortgage['Cumulative_Rent_Income'] - yearly_mortgage['Cumulative_Tax_Savings']
        yearly_mortgage['House_Net_Value'] = yearly_mortgage['Total_Equity_With_Appreciation'] - yearly_mortgage['Effective_Cost']


        # Opportunity Costs
        yearly_mortgage['Initial_Opportunity'] = ((down_payment+closing_buy)*offer) * (1 + investment_return)**(yearly_mortgage['Year']) * (1-long_term_capital_gains) # investing the downpayment and the closing cost of buying
        yearly_mortgage['Yearly_Rent_Cost'] = 12 * opportunity_rent * ((1 + rent_yearly_increase) ** yearly_mortgage['Year']) # The cost of renting

        # Leftover money to invest if you choose to rent instead of buy, can be negative which means renting is more expensive than buying on a month-to-month basis
        yearly_mortgage['Extra_Investing_Money'] = p * 12+ yearly_mortgage['HOA']+ yearly_mortgage['Property_Tax']+ yearly_mortgage['Homeowner_Insurance']+ yearly_mortgage['Maintenance']- yearly_mortgage['Rent_Income']- yearly_mortgage['Effective_Tax_Savings']- yearly_mortgage['Yearly_Rent_Cost']

        #Invest the extra money saved by renting instead of buying
        yearly_growth = np.array([])
        for year in range(1,1 + time): #Take the extra investing money each year and invest it
            growth_years = yearly_mortgage[yearly_mortgage.Year <= year][['Year','Extra_Investing_Money']]
            growth_years['Years_Investing'] = np.array(growth_years.Year)[::-1] - 1 # The extra money is what you have at the end of the year, so at year 3, you would have invested the year 1 money for 2 years
            growth_years['Growth'] = growth_years['Extra_Investing_Money'] * (1 + investment_return) ** growth_years['Years_Investing']
            yearly_growth = np.append(yearly_growth,np.array([growth_years.Growth.sum()]))
            
        yearly_mortgage['Total_Investment'] = yearly_growth * (1 - long_term_capital_gains)
        yearly_mortgage['Rent_Net_Value'] = yearly_mortgage['Initial_Opportunity'] + yearly_mortgage['Total_Investment']
        yearly_mortgage['Opportunity_Cost'] = yearly_mortgage['Rent_Net_Value'] - yearly_mortgage['House_Net_Value']

        self.Plot_Data = yearly_mortgage[['Year','House_Net_Value','Rent_Net_Value','Opportunity_Cost']]
     

