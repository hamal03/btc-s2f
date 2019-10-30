# Bitcoin Stock to Flow

Medium blogger [PlanB](https://medium.com/@100trillionUSD) created a 
[model](https://medium.com/@100trillionUSD/modeling-bitcoins-value-with-scarcity-91fa0fc03e25)
which got some international traction. The model shows that the Bitcoin price
seems to follow a power law, based on its scarcity which can be expressed as
the ratio between its stock and flow.

I collect data on a granularity of 1 day from
[coinmetric.io](https://coinmetrics.io/community-network-data/) and calculate the ratio
based on the real number of bitcoins that were mined for all of Bitcoin's
history until the day of data gathering and extrapolate it into the future based
on mining 144 blocks per day. The actual data is kept in a SQLite database which is 
added to as needed. The data is used by a Python script to calculate the R squared
value and the root mean sqared error of the logarithm of the stock to flow ratio
and the logarithm of the bitcoin price in US dollars. The data points that are 
included in the analysis are all dates, prices and total number of bitcoins
where the price is non-zero. The flow is calculated as the added number of coins
that lead to the total at a specific time during 365 days.

The SQLite database is pretty simple and has the following schema:
<pre>
CREATE TABLE btc ( date int PRIMARY KEY, price float, coins float );
</pre>
The date is the integer of the epoch time divided by 86400. This is to enforce 
a daily granularity and prevend introduction of spurious data.

The script generates 4 files:
* gpvars.txt: this file cointains a number of values that are read in the gnuplot
script like the R2 and RMSE values, the slope and intercept of the regression line etc.
* sftime.csv: a comma seperated file with the data points for the two timeline charts
* sfdata.csv: a comma seperated file to generate the points and regression line 
of the s2f and price logarithm values
* bashvars.sh: a few prices of the latest data point with which the HTML file 
containing the graphs can be adjusted.

These scripts are used daily to generate three charts that are presented on 
[this web page](https://s2f.hamal.nl/s2fcharts.html).
