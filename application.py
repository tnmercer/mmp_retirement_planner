# Imports
import pandas as pd
import numpy as np
from pathlib import Path
import hvplot.pandas
import matplotlib.pyplot as plt
from pandas.tseries.offsets import DateOffset
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from sklearn import svm

from utils import *



# this function loads the price data for a particular ticker
# it returns a dataframe with a Datetime index columns, and 
# Open, High, Low, Closed, and Volume columns
def load_csv(ticker):
	
	# load the ticker data
	# df = load_data(ticker, set_index=True, index_column='Date')
	df = load_data(ticker)
	
	# check if the first date index is less than 2012-01-01
	if df.index[0] < pd.Timestamp('2012-01-01'):
		# if so, drop all date rows before January 01, 2012
		# we're performing this step so all stock data starts
		# at the same time
		df = df[df.index > pd.Timestamp('2012-01-01')]
		
		# then check if 'Adj Close' and 'Ret_Index' columms exist
		# if so, remove them from the dataframe
		if {'Adj Close'}.issubset(df.columns):
			df = df.drop(columns='Adj Close')
		if {'Ret_Index'}.issubset(df.columns):
			df = df.drop(columns='Ret_Index')
		
		# then save the modified dataframe back to CSV
		save_data(df, filename=ticker+'.csv')
	
	# now return the modified dataframe
	return df


def resample_dataframe(df):

	df_to_resample = df.copy()
	# drop 'Adj Close' and 'Ret_Index' columms if they exist
	if {'Adj Close'}.issubset(df_to_resample.columns):
		df_to_resample = df_to_resample.drop(columns='Adj Close')
	if {'Ret_Index'}.issubset(df_to_resample.columns):
		df_to_resample = df_to_resample.drop(columns='Ret_Index')
	
	how_to_resample = {
        'Open':'first',
        'High':'max',
        'Low':'min',
        'Close':'last',
        'Volume':'sum'
    }
	
	resampled_df = None
	resampled_df = df_to_resample.resample('1M').agg(how_to_resample)
	
	return resampled_df


# this function prepares the stock data for machine learning
# it generates 
def prep_data_for_ML(df):
	
	df['Current Return'] = df['Close'].pct_change()
	df['Future Returns'] = df['Close'].pct_change().shift(-3)

	df['Future Target'] = 0.0
	df.loc[(df['Future Returns'] >= 0), 'Future Target'] = 1
	df.loc[(df['Future Returns'] < 0), 'Future Target'] = -1
	
	df = df.dropna()
	
	return df


def predict_future(monthly_df, current_date=pd.Timestamp('2020-01-31')):
	
	# TODO: moving this code into an initialization function
	# daily_df = load_csv(ticker)
	# monthly_df =  resample_dataframe(daily_df)
	
	# commenting this code because we should provide a current_date each time
	# this function is run
	# current_date = monthly_df.index.max() - DateOffset(months=12)

	debug_print(f'current date is {current_date}')

	training_begin = None
	training_end = None
	test_begin = None
	test_end = None

	# calculating the beginning and end of our train and test time frames
	training_begin = monthly_df.index.min()
	# training_end = current_date - DateOffset(months=3)
	training_end = current_date - DateOffset(3)
	test_begin = training_end + DateOffset(1)
	test_end   = current_date

	debug_print(f'training begin: {training_begin}')
	debug_print(f'training end: {training_end}')
	debug_print(f'test begin: {test_begin}')
	debug_print(f'test begin: {test_end}')

	# commented out because we run this code once at the beginning
	# this preps our dataframe for our ML pass
	# monthly_df = prep_data_for_ML(prep_data_for_ML)

	# creating our X (features) and y (prediction) dataframes
	X = monthly_df.drop(columns=['Open','High', 'Low','Current Return','Future Returns','Future Target'])
	y = monthly_df['Future Target']
	
	# creating our training and testing sub-sets
	X_train = X.loc[training_begin:training_end]
	y_train = y.loc[training_begin:training_end]
	X_test = X.loc[test_begin:test_end]
	y_test = y.loc[test_begin:test_end]

	debug_print(X_train.tail(10))
	debug_print(y_train[-10:])
	debug_print(X_test.tail(10))
	debug_print(y_test[-10:])

	# scale the features we provide to our model
	scaler = StandardScaler()
	X_scaler = scaler.fit(X_train)
	X_train_scaled = X_scaler.transform(X_train)
	X_test_scaled = X_scaler.transform(X_test)

	# create our model, fit, and predict the future (next 3 months)
	svm_model = svm.SVC()
	svm_model = svm_model.fit(X_train_scaled, y_train)
	y_future_prediction = svm_model.predict(X_test_scaled)

	debug_print(y_future_prediction)

	return y_future_prediction


# TODO: we need to finish the implementation of this function
# it should take the future prediction, and last_investment_date and
# return the number of months to invest

def calculate_investment_from_prediction(y_future_prediction):

	# determine how many months to invest
	months_to_invest = 0
	
	# for each prediction, add a month's worth of investing 
	for prediction in y_future_prediction:
		if prediction > 0:
			months_to_invest += 1
		else:
			break

	# TODO: similar to the above, we need to calculate months since last investment
	# then add that number to months_to_invest

	return months_to_invest


# TODO: save our future predictions so we can graph them later
def save_monthly_predictions(current_date, close, current_return, y_future_prediction):

	# create a datafrom to hold this months predictions
	current_month_df = pd.DataFrame(columns=['Date','Close'])
	current_month_df.set_index('Date')
	current_month_df.index[0]=current_date
	current_month_df.Close[0]=close
	current_month_df.index[1]=current_date + DateOffset(1)
	current_month_df.Close[1]=current_return * y_future_prediction[0] + close
	current_month_df.index[2]=current_date + DateOffset(2)
	current_month_df.Close[2]=current_return * y_future_prediction[1] + current_month_df.Close[1]
	current_month_df.index[3]=current_date + DateOffset(3)
	current_month_df.Close[3]=current_return * y_future_prediction[2] + current_month_df.Close[2]
	
	# TODO: append current_month_df to a monthly_predictions_list
	
	return None




def main():
	# load the VTI total market ETF and resample the daily data to monthly
	total_market_df = resample_dataframe(load_csv('VTI'))
	#
	total_market_df = prep_data_for_ML(total_market_df)

	# save current_date (to remember where we are in time)
	# save current_date_idx = 12
	# make current_date = total_market_df.index[12]

	# we need the last_investment_date so we know how many months to invest
	# this needs to be moved into Toni's code
	global last_investment_date
	last_investment_date = None

	# for each month, calculate our future predictions and invest if appropriate
	for current_date in total_market_df.index:

		# skip the first 12 months
		if current_date < total_market_df.index[12]:
			continue

		# get our future predictions
		y_future_prediction = predict_future(total_market_df, current_date)

		# save our current months predictions for later plotting
		# NOTE: save_monthly_predictions function is INCOMPLETE, see above
		save_monthly_predictions(
			current_date,
			total_market_df[current_date]['Close'],
			total_market_df[current_date]['Current Return'],
			y_future_prediction)
		
		# calculate how many months we can invest
		# NOTE: calculate_investment_from_prediction function is INCOMPLETE, see above
		months_to_invest = calculate_investment_from_prediction(y_future_prediction)

		# TODO @Toni we're waiting for you to create this function
		# this function should...
		# - update the portfolio returns each month
		# - invest-and-rebalance at the same time if months_to_invest is positive
		# update_portfolio(current_date, this_months_return, months_to_invest)