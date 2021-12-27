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
# Extend five years in the future
extendto =  int(datetime.now().timestamp()) + 153878400

conn = sqlite3.connect('bcinfo.sqlite')
cur = conn.cursor()
cur.execute('select * from btc order by date')
bstr = cur.fetchall()
maxdt = bstr[-1][0]

if "--regen" not in sys.argv:
    burl = 'https://community-api.coinmetrics.io/v4/timeseries/asset-metrics'
    bapistr = '?assets=btc&frequency=1d&metrics=PriceUSD%2CSplyCur&start_time='
    tdago = datetime.fromtimestamp(bstr[-3][0]*86400).strftime('%F')
    newdata = requests.get(burl+bapistr+tdago)
    if newdata.status_code != 200:
        print("Getting data from coinmetrics failed")
        sys.exit(1)
    jdata = json.loads(newdata.text)
    for bd in jdata['data']:
        if bd['PriceUSD'] is None or bd['SplyCur'] is None: break
        epdate = int(int(datetime.strptime(bd['time'], '%Y-%m-%dT%H:%M:%S.000000000Z').\
            strftime('%s'))/86400+.5)
        if epdate <= maxdt: continue
        newentry = (epdate, float(bd['PriceUSD']), float(bd['SplyCur']))
        cur.execute('insert into btc values (?,?,?)', newentry)
        bstr.append(newentry)
    if maxdt == bstr[-1][0]: sys.exit()
    conn.commit()
    maxdt = bstr[-1][0]

dt = list()
coins = list()
height = list()
price = list()
sf = list()
lnsf = list()
lnprice = list()

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
    if coins[j] >= ncoins + 210000*50/2**p:
        ncoins += 210000*50/2**p
        p += 1
    height.append(210000*p+(coins[j]-ncoins)*2**p/50)
    sf.append(coins[j]/(coins[j]-bstr[i-365][2]))
    # Calculate ln(S2F) and ln(price)
    # ln() values should be in 2D list for sklearn
    lnsf.append([np.log(sf[j])])
    lnprice.append([np.log(price[j])])
    j += 1

# Remember the current length of sf[]
lstsf=len(sf)

# extend the lists of coins, height and date into the future
# based on 144 blocks per day
while dt[-1] < extendto:
    dt.append(dt[-1]+86400)
    height.append(height[-1]+144)
    # Did we cross a halving point?
    if int(height[-1]/210000) > p:
        ncoins += 210000*50/2**p
        p += 1
    coins.append(ncoins+(height[-1]%210000)*50/2**p)
    sf.append(coins[-1]/(coins[-1]-coins[-361]))

# scikit-learn regression
# Model initialization
regression_model = LinearRegression()
# Fit the data(train the model)
regression_model.fit(lnsf, lnprice)
# Predict
lnpr_pred = regression_model.predict(lnsf)

# model evaluation
rmse = mean_squared_error(lnprice, lnpr_pred)
r2 = r2_score(lnprice, lnpr_pred)
slope = regression_model.coef_[0][0]
intercept = regression_model.intercept_[0]
e2rmse = np.exp(rmse)
e2intc = np.exp(intercept)

# Calculate min and max Y values for detail chart
detymax = 0
detymin = 10**15
for i in range(maxdt-731, maxdt):
    detymax = max(detymax, sf[lstsf+i-maxdt-1]**slope*e2intc*e2rmse*2, price[i-maxdt-1])
    detymin = min(detymin, sf[lstsf+i-maxdt-1]**slope*e2intc/e2rmse/2, price[i-maxdt-1])
for i in range(maxdt, maxdt+61):
    detymax = max(detymax, sf[lstsf+i-maxdt-1]**slope*e2intc*e2rmse*2)
    detymin = min(detymin, sf[lstsf+i-maxdt-1]**slope*e2intc/e2rmse/2)
detymax *= 1.5
detymin /= 1.5
# Calculate position of text & box
yrange = np.log(detymax/detymin)
detybox = np.exp(boxfact*yrange) * detymin
detytxt = np.exp(textfact*yrange) * detymin

# Gnuplot variable values
gpvars = open('gpvars.txt', 'w')
gpvars.write(str(round(slope, 2))+"\n")
gpvars.write(str(round(e2intc, 2))+"\n")
gpvars.write(str(round(rmse, 4))+"\n")
gpvars.write(str(round(r2, 4))+"\n")
gpvars.write(str(round(e2rmse, 2))+"\n")
gpvars.write(str(int(maxdt*86400))+"\n")
gpvars.write(str((0.01/e2intc)**(1/slope))+"\n") # Low S2F val for y2 axis
gpvars.write(str((ymax/e2intc)**(1/slope))+"\n") # High S2F val for y2 axis
gpvars.write(str(ymax)+"\n")
gpvars.write(str(round(intercept, 2))+"\n")
gpvars.write(str(int((maxdt-731)*86400))+"\n")
gpvars.write(str(int((maxdt+61)*86400))+"\n")
gpvars.write(str(detymax)+"\n") # High value of detail chart Y axis
gpvars.write(str(int((maxdt-480)*86400))+"\n")
gpvars.write(str(detymin)+"\n") # Low value of detail chart Y axis
gpvars.write(str(detybox)+"\n") # Y value of box object
gpvars.write(str(detytxt)+"\n") # Y value of box label
gpvars.close()

for i in range(len(price), len(dt)):
    price.append("")

# Gnuplot data for timeline chart
gpdata = open('sftime.csv', 'w')
for i in range(len(dt)):
    sfval = sf[i]**slope*e2intc
    sd1p = sfval*e2rmse
    sd2p = sd1p*2
    sd1m = sfval/e2rmse
    sd2m = sd1m/2
    gpdata.write(",".join(str(x) for x in [dt[i], sfval, sd1p, sd2p, sd1m, sd2m, price[i]])+"\n")
gpdata.close()

# Gnuplot regression line values
sfdata = open("sfdata.csv", "w")
for i in range(len(lnsf)):
    sfdata.write(str(lnsf[i][0]) + "," + str(lnprice[i][0]) +"\n")
sfdata.close()

# Shell script values for table
idx = len(lnprice)-1
bashvar = open("bashvar.sh", "w")
bashvar.write("SFDT="+str(dt[idx])+"\n")
bashvar.write("SFCP="+str(round(float(price[idx]), 2))+"\n")
bashvar.write("SFPP="+str(round(float(sf[idx]**slope*e2intc), 2))+"\n")
bashvar.write("SFPP1="+str(round(float(sf[idx]**slope*e2intc*e2rmse), 2))+"\n")
bashvar.write("SFPM1="+str(round(float(sf[idx]**slope*e2intc/e2rmse), 2))+"\n")
bashvar.write("SFPP2="+str(round(float(sf[idx]**slope*e2intc*e2rmse*2), 2))+"\n")
bashvar.write("SFPM2="+str(round(float(sf[idx]**slope*e2intc/e2rmse/2), 2))+"\n")
bashvar.close()

if "--quiet" not in sys.argv:  print("Data files created")

