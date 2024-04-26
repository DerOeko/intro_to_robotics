import pandas as pd
import matplotlib.pyplot as plt

#read from error.csv file
#     global dataframe
dataframe = pd.read_csv('error.csv')
#plot the error values
plt.plot(dataframe['error'])
plt.show()
