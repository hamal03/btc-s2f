# calculate regression lines in different subsets from
# Bitcoin's stock-to-flow history
# Written by Rob Wolfram (Twitter: @hamal03)

import json
from datetime import datetime
import requests
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

cmurl = "https://community-api.coinmetrics.io/v2/assets/btc/metricdata"
cmapistr = '?metrics=PriceUSD%2CSplyCur%2CBlkCnt&start=2009-01-01'
cmdata = requests.get(cmurl+cmapistr)
jdata = json.loads(cmdata.text)

## Reusing pre-downloaded data from coinmetrics
#cmdl = open('/var/tmp/coinmetrics.json', 'r')
#cmdata = '\n'.join(cmdl.readlines())
#cmdl.close()
#jdata = json.loads(cmdata)

cutoffday = 18231 # 2019-12-01
startdate = 14808 # 2010-07-17, first date with known value
halving1 = 15672  # 2012-11-28, first halving event
halving2 = 16991  # 2016-07-09, second halving event

# bdata structure:
# bdata[epdate] = [ price, stock, blockheight, s2f, ln(s2f), ln(price) ]
# epdate = round(epoch/86400)

bdata = dict()
for cm in jdata['metricData']['series']:
    if cm['values'][0] is None: cm['values'][0] = 0
    if cm['values'][1] is None or cm['values'][1] == 0: continue
    epdate = int(int(datetime.strptime(cm['time'], '%Y-%m-%dT%H:%M:%S.000Z').\
        strftime('%s'))/86400+.5)
    if (epdate-1) in bdata:
        blktotal = bdata[epdate-1][2] + int(float(cm['values'][2]))
    else:
        blktotal = int(float(cm['values'][2]))
    bdata[epdate] = [float(cm['values'][0]), float(cm['values'][1]), blktotal]

for k in bdata.keys():
    if k < startdate: continue
    flow = bdata[k][1] - bdata[k-365][1]
    s2f = bdata[k][1] / flow
    lnsf = np.log(s2f)
    lnpr = np.log(bdata[k][0])
    bdata[k] += [s2f, lnsf, lnpr]

startprice = bdata[startdate][0]
lnstartpr = bdata[startdate][5]

hist = {
    'current': list(range(halving2+365, cutoffday)),
    'alltime': list(range(startdate, cutoffday)),
    'nearall': list(range(startdate, halving2+365)),
    'first2': list(range(startdate, halving2)),
    'first': list(range(startdate, halving1)),
    'second': list(range(halving1+1, halving2)),
    's2fonly': list(range(halving1-365, halving1+365)) + \
       list(range(halving2-365, halving2+365)),
    'nots2f': list(range(startdate, halving1-365)) + \
       list(range(halving1+365, halving2-365)),
    }

dstitle = {
    "alltime": "dummy title",
    "nearall": "All time for reference",
    "first2": "First two halving periods",
    "first": "First halving period only",
    "second": "Second halving period only",
    "s2fonly": "Time around halving events",
    "nots2f": "Not the time around halvings",
    }

# currdata.tsv: epoch \t price \t s2f \t ln(s2f) \t ln(price)
currdata = open('currdata.tsv', 'w')
lncurpric = list()
for dt in hist['current']:
    lncurpric.append([bdata[dt][5]])
    currdata.write(str(dt*86400)+'\t'+str(bdata[dt][0])+'\t'+str(bdata[dt][3])+ \
        '\t'+str(bdata[dt][4])+'\t'+str(bdata[dt][5])+'\n')
currdata.close()
avglncurpr = np.average(lncurpric)

# table data
tbldata = dict()
tbldata['headers'] = ['lnstart', 'lnpred', 'lnact', 'lndiff',\
    'realstart', 'realpred', 'realact', 'growthdiff', 'r2ref', 'r2alltime']

for dset in hist.keys():
    if dset == 'current': continue
    lnsf = list()
    lnprice = list()
    regmod = LinearRegression()
    # fill two double arrays with ln(s2f) and ln(price) of historical data
    # and create historical data set for plot
    dataout = open(dset+'-data.tsv', 'w')
    for dt in hist[dset]:
        lnsf.append([bdata[dt][4]])
        lnprice.append([bdata[dt][5]])
        dataout.write(str(dt*86400)+'\t'+str(bdata[dt][0])+'\t'+str(bdata[dt][3])+ \
            '\t'+str(bdata[dt][4])+'\t'+str(bdata[dt][5])+'\n')
    dataout.close()
    # Fit the data
    regmod.fit(lnsf, lnprice)
    # Calculate prediction
    lnpred = regmod.predict(lnsf)
    # Evaluate historical data
    slope = regmod.coef_[0][0]
    intercept = regmod.intercept_[0]
    r2hist = r2_score(lnprice, lnpred)
    #
    # Create a new 'history' with real data until the maximum of the set
    # and extrapolate to "full history" based on 144 blocks per day
    # keep real price and real lnprice
    # Create datafile with calculated parameters
    startexpol = np.max(hist[dset])+1
    fakebd = dict()
    lnatpric = list()
    lnatpred = list()
    testsetlnpr = list()
    fakeatdata = open(dset+'-alltime.tsv', 'w')
    for dt in range(startdate, startexpol):
        fakebd[dt] = bdata[dt]
        lnatpric.append([fakebd[dt][5]])
        lnatpred.append([fakebd[dt][4]*slope+intercept])
        predprice = fakebd[dt][3]**slope*np.exp(intercept)
        fakeatdata.write(str(dt*86400)+'\t'+str(predprice)+'\n')
    for dt in range(startexpol, cutoffday):
        if fakebd[dt-1][2] < 209856:
            stock = fakebd[dt-1][1] + 144 * 50
        elif fakebd[dt-1][2] >= 210000 and fakebd[dt-1][2] < 419856:
            stock = fakebd[dt-1][1] + 144 * 25
        elif fakebd[dt-1][2] >= 420000:
            stock = fakebd[dt-1][1] + 144 * 12.5
        elif fakebd[dt-1][2] >= 209856 and fakebd[dt-1][2] < 210000:
            stock = fakebd[dt-1][1] + (210000-fakebd[dt-1][2])*50 + (fakebd[dt-1][2]-209856)*25
        elif fakebd[dt-1][2] >= 419856 and fakebd[dt-1][2] < 420000:
            stock = fakebd[dt-1][1] + (420000-fakebd[dt-1][2])*25 + (fakebd[dt-1][2]-419856)*12.5
        fakes2f = stock / (stock - fakebd[dt-365][1])
        lnfks2f = np.log(fakes2f)
        fakebd[dt] = [bdata[dt][0], stock, bdata[dt][2]+144, fakes2f, lnfks2f, bdata[dt][5]]
        lnatpric.append([fakebd[dt][5]])
        lnatpred.append([fakebd[dt][4]*slope+intercept])
        predprice = fakebd[dt][3]**slope*np.exp(intercept)
        fakeatdata.write(str(dt*86400)+'\t'+str(predprice)+'\n')
        if dt in hist['current']: testsetlnpr.append(fakebd[dt][4]*slope+intercept)
    fakeatdata.close()
    r2fakedata = r2_score(lnatpric, lnatpred)
    sefakedata = mean_squared_error(lnatpric, lnatpred)
    e2se = np.exp(sefakedata)
    # Calculate average predicted price from test set
    # conditional is to prevend warning
    if dset != 'alltime':
        lnpredavg = np.average(testsetlnpr)
    else:
        lnpredavg = avglncurpr
    #
    # Fill arrays with current data
    # ['nearall', 'first2', 'first', 'second', 's2fonly', 'nots2f']:
    lncurpred = list()
    for dt in hist['current']:
        lncurpred.append([bdata[dt][4]*slope+intercept])
    r2curr = r2_score(lncurpric, lncurpred)

    varout = open(dset+'-vars.txt', 'w')
    varout.write(dstitle[dset]+"\n")
    varout.write(str(slope)+"\n")
    varout.write(str(intercept)+"\n")
    varout.write(str(np.exp(intercept))+"\n")
    varout.write(str(r2hist)+"\n")
    varout.write(str(r2fakedata)+"\n")
    varout.write(str(e2se)+"\n")
    varout.write(str(sefakedata)+"\n")
    varout.close()
    # 
    #tbldata['headers'=['lnstart','lnpred','lnact','lndiff',
    #    'realstart','realpred','realact','growthdiff','r2ref','r2alltime']

    lnstart = bdata[hist[dset][0]][5]
    realstart = bdata[hist[dset][0]][0]
    lndiff = (lnpredavg-lnstart)/(avglncurpr-lnstart)-1
    realpred = np.exp(lnpredavg)
    realact = np.exp(avglncurpr)
    growthdiff = np.exp(lndiff)-1
    tbldata[dset] = [lnstart, lnpredavg, avglncurpr, lndiff,\
        realstart, realpred, realact, growthdiff, r2hist, r2fakedata]

tblout = open("tabledata.tsv", "w")
tblout.write('data set\t'+'\t'.join(tbldata['headers'])+"\n")
for dset in  hist.keys():
    if dset == 'current' or dset == "alltime": continue
    strout = dstitle[dset]
    for val in tbldata[dset]:
        strout += '\t' + str(val)
    tblout.write(strout+'\n')
tblout.close()
