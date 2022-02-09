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
```
CREATE TABLE btc ( date int PRIMARY KEY, price float, coins float );
```
The date is the integer of the epoch time divided by 86400. This is to enforce 
a daily granularity and prevend introduction of spurious data.

If the SQLite database file does not exist, the script will create it and pull
the data from coinmetric.io starting at Jan 3th, 2009.

The script generates 4 files:

* gpvars.txt: this file cointains a number of values that are read in the gnuplot
script like the R2 and RMSE values, the slope and intercept of the regression line etc.
* sftime.csv: a comma seperated file with the data points for the two timeline charts
* sfdata.csv: a comma seperated file to generate the points and regression line 
of the s2f and price logarithm values
* bashvars.sh: a few prices of the latest data point with which the HTML file 
containing the graphs can be adjusted.

These files are used daily to generate three charts that are presented on 
[this web page](https://s2f.hamal.nl/s2fcharts.html).

## Containerising

The script to generate the daily graphs for the web page used to run on an older
Ubuntu version ans because I have some bad experiences with the consistency of
Gnuplot between versions, I decided to put it all in a container. The Dockerfile
to create the container is provided as well. Though it's based on Alpine Linux,
it still installs Python3 with some large modules, Gnuplot, fonts and
Imagemagick, so the image is still a whopping 521 MB.

The Python and Gnuplot scripts are not included in the container, they should be
present on persistent storage that you mount on /data in the container. The
container will also read if there are cron files in the /data/cron.d directory
and use those to schedule a script to run. I use that to run the script that
generates and uploads the data for the web site but other combinations for
generating Gnuplot images with Python output are possible as well.

The container can be build with docker using
```
docker build -f Containerfile -t <imagetag> .
```
or with buildah using
```
buildah bud -f Containerfile -t <imagetag>
```

You can the use docker or podman to run the image with:
```
docker run -d -v /some/data/path:/data <imagetag>
```

I prefer podman because it's daemonless and I can (and do) run the container as
an oridinary user. I run it on an EL8 system ([Rocky Linux](https://rockylinux.org/))
so I get the added security of containment with SELinux and control with
systemd.

## Tech details

The python script is using python 3.9.5 and the following extra modules:
* numpy
* requests
* sklearn.linear_model
* sklearn.metrics

Gnuplot is version 5.4.




