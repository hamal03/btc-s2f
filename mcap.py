# This python script will calculate the statistical
# correlation between Bitcoin's "stock to flow" model
# by the pseudonymous user "PlanB". De calculation is based on
# daily price averages from blockstream.info.
# The output serves as input data for a gnuplot script.
# 
# Call the script with "--regen" to generate new data even
# if no new data is available at blockstream

# imports
import sys
import numpy as np
import sqlite3
import requests
import json
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# gnuplot price range max
ymax = 5000000

# Needed for position of te text box on the detail chart
boxfact=.942
textfact=.963

# Date to which we exend the blocks based on 144 blocks per day
extendto = 1798758000 # 2027-01-01

conn = sqlite3.connect('bcinfo.sqlite')
cur = conn.cursor()
cur.execute('select * from btc order by date')
bstr = cur.fetchall()
maxdt = bstr[-1][0]

#if "--regen" not in sys.argv:
#    burl = "https://community-api.coinmetrics.io/v2/assets/btc/metricdata"
#    bapistr = '?metrics=PriceUSD%2CSplyCur&start='
#    tdago = datetime.fromtimestamp(bstr[-3][0]*86400).strftime('%F')
#    newdata = requests.get(burl+bapistr+tdago)
#    if newdata.status_code != 200:
#        print("Getting data from coinmetrics failed")
#        sys.exit(1)
#    jdata = json.loads(newdata.text)
#    for bd in jdata['metricData']['series']:
#        if bd['values'][0] is None or bd['values'][1] is None: break
#        epdate = int(int(datetime.strptime(bd['time'], '%Y-%m-%dT%H:%M:%S.000Z').\
#            strftime('%s'))/86400+.5)
#        if epdate <= maxdt: continue
#        newentry = (epdate, float(bd['values'][0]), float(bd['values'][1]))
#        cur.execute('insert into btc values (?,?,?)', newentry)
#        bstr.append(newentry)
#    if maxdt == bstr[-1][0]: sys.exit()
#    conn.commit()
#    maxdt = bstr[-1][0]

dt = list()
coins = list()
height = list()
price = list()
mcap = list()
sf = list()
lnsf = list()
lnprice = list()
lnmcap = list()

p = 0 # halving period
ncoins = 0 #number of coins in beginning of this period

# Read available data and calculate stock to flow (current coins
# divided by last year's additions.
j = 0 # use second index to take skipped records into account
for i in range(len(bstr)):
    if bstr[i][1] == 0: continue
    dt.append(bstr[i][0]*86400)
    price.append(bstr[i][1])
    coins.append(bstr[i][2])
    mcap.append(bstr[i][1]*bstr[i][2])
    if coins[j] >= ncoins + 210000*50/2**p:
        ncoins += 210000*50/2**p
        p += 1
    height.append(210000*p+(coins[j]-ncoins)*2**p/50)
    sf.append(coins[j]/(coins[j]-bstr[i-365][2]))
    # Calculate ln(S2F) and ln(price)
    # ln() values should be in 2D list for sklearn
    lnsf.append([np.log(sf[j])])
    lnprice.append([np.log(price[j])])
    lnmcap.append([np.log(mcap[j])])
    j += 1

# Remember the current length of sf[]
lstsf=len(sf)

## extend the lists of coins, height and date into the future
## based on 144 blocks per day
#while dt[-1] < extendto:
#    dt.append(dt[-1]+86400)
#    height.append(height[-1]+144)
#    # Did we cross a halving point?
#    if int(height[-1]/210000) > p:
#        ncoins += 210000*50/2**p
#        p += 1
#    coins.append(ncoins+(height[-1]%210000)*50/2**p)
#    sf.append(coins[-1]/(coins[-1]-coins[-361]))

# scikit-learn regression
# Model initialization on price
prc_reg_model = LinearRegression()
# Fit the data(train the model)
prc_reg_model.fit(lnsf, lnprice)
# Predict
lnprc_pred = prc_reg_model.predict(lnsf)

# model evaluation
prc_rmse = mean_squared_error(lnprice, lnprc_pred)
prc_r2 = r2_score(lnprice, lnprc_pred)
prc_slope = prc_reg_model.coef_[0][0]
prc_intercept = prc_reg_model.intercept_[0]
prc_e2rmse = np.exp(prc_rmse)
prc_e2intc = np.exp(prc_intercept)

# scikit-learn regression
# Model initialization on price
cap_reg_model = LinearRegression()
# Fit the data(train the model)
cap_reg_model.fit(lnsf, lnmcap)
# Predict
lncap_pred = cap_reg_model.predict(lnsf)

# model evaluation
cap_rmse = mean_squared_error(lnmcap, lncap_pred)
cap_r2 = r2_score(lnmcap, lncap_pred)
cap_slope = cap_reg_model.coef_[0][0]
cap_intercept = cap_reg_model.intercept_[0]
cap_e2rmse = np.exp(cap_rmse)
cap_e2intc = np.exp(cap_intercept)

# Gnuplot variable values
gpvars = open('gpvars.txt', 'w')
gpvars.write(str(round(prc_slope, 2))+"\n")
gpvars.write(str(round(prc_e2intc, 2))+"\n")
gpvars.write(str(round(prc_rmse, 4))+"\n")
gpvars.write(str(round(prc_r2, 4))+"\n")
gpvars.write(str(round(prc_e2rmse, 2))+"\n")
gpvars.write(str(int(maxdt*86400))+"\n")
gpvars.write(str((0.01/prc_e2intc)**(1/prc_slope))+"\n") # Low S2F val for y2 axis
gpvars.write(str((ymax/prc_e2intc)**(1/prc_slope))+"\n") # High S2F val for y2 axis
gpvars.write(str(ymax)+"\n")
gpvars.write(str(round(prc_intercept, 2))+"\n")
gpvars.write(str(round(cap_slope, 2))+"\n")
gpvars.write(str(round(cap_e2intc, 2))+"\n")
gpvars.write(str(round(cap_rmse, 4))+"\n")
gpvars.write(str(round(cap_r2, 4))+"\n")
gpvars.write(str(round(cap_e2rmse, 2))+"\n")
gpvars.write(str(round(cap_intercept, 2))+"\n")
gpvars.close()

for i in range(len(price), len(dt)):
    price.append("")

# Gnuplot data for timeline chart
gpdata = open('sftime.csv', 'w')
for i in range(len(dt)):
    prc_sfval = sf[i]**prc_slope*prc_e2intc
    prc_sd1p = prc_sfval*prc_e2rmse
    prc_sd2p = prc_sd1p*2
    prc_sd1m = prc_sfval/prc_e2rmse
    prc_sd2m = prc_sd1m/2
    cap_sfval = sf[i]**cap_slope*cap_e2intc/coins[i]
    cap_v_prc = cap_sfval / prc_sfval
    gpdata.write(",".join(str(x) for x in [dt[i], prc_sfval, prc_sd1p, prc_sd2p, \
        prc_sd1m, prc_sd2m, price[i], cap_sfval, cap_v_prc])+"\n")
gpdata.close()

# Gnuplot regression line values
sfdata = open("sfdata.csv", "w")
for i in range(len(lnsf)):
    sfdata.write(str(lnsf[i][0]) + "," + str(lnprice[i][0]) \
        + "," + str(lnmcap[i][0]) +"\n")
sfdata.close()

if "--quiet" not in sys.argv:  print("Data files created")

