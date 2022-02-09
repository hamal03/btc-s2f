#!/bin/sh
PATH=/bin:/usr/bin ; export PATH
SSHOPTS="-q -i /data/.ssh/id_s2fgen -o UserKnownHostsFile=/data/.ssh/knownhosts"

cd $(dirname $0)

[ -f README.md ] || touch -d 1971-01-01 README.md

if [ ! -s bashvar.sh -o ! -s sfdata.csv -o ! -s sftime.csv ] ; then
    FORCE="--force"
fi
python gens2fdata.py $FORCE --quiet 2>/dev/null
if [ $? -ne 0 ] ; then
    echo "Python script failed"
    exit 1
elif [ $(stat -c %Y sfdata.csv) -gt $(stat -c %Y README.md) ] ; then
    gnuplot stock2flowcharts.gpl >/dev/null 2>&1
else
    exit 0
fi

if [ $? -ne 0 ] ; then
    echo "Gnuplot failed"
    exit 1
elif [ $(stat -c %Y alltimeprice.svg) -gt $(stat -c %Y README.md) ] ; then
    for i in alltimeprice.svg detailprice.svg stock2flow.svg ; do
        convert $i ${i%.svg}.png || {
            echo "convert failed on $i"
            rm -f alltimeprice.png detailprice.png stock2flow.png 2>/dev/null
            exit 1
        }
    done
else
    # should not happen
    exit 0
fi

if [ -e alltimeprice.png -a -e detailprice.png -a -e stock2flow.png -a \
        $(stat -c %Y alltimeprice.png) -gt $(stat -c %Y README.md) ] ; then
    # This is where we upload the images and adjusted HTML file to the site
    # source ./bashvar.sh && \
    #     sed -i -e "s/--FD-->.*<!/--FD-->$(date -d @$SFDT '+%A %d %B %Y')<!/" \
    #     -e "s/--DT-->.*<!/--DT-->$(date -d @$SFDT +%F)<!/" \
    #     -e "s/--CP-->.*<!/--CP-->\$$SFCP<!/" \
    #     -e "s/--PP-->.*<!/--PP-->\$$SFPP<!/" \
    #     -e "s/--PP1-->.*<!/--PP1-->\$$SFPP1<!/" \
    #     -e "s/--PM1-->.*<!/--PM1-->\$$SFPM1<!/" \
    #     -e "s/--PP2-->.*<!/--PP2-->\$$SFPP2<!/" \
    #     -e "s/--PM2-->.*<!/--PM2-->\$$SFPM2<!/" \
    #     s2fcharts.html && \
    #     echo 'put *.png' | sftp $SSHOPTS s2f@s2f.hamal.nl:html/images/. >/dev/null && \
    #     echo 'put s2fcharts.html' | sftp $SSHOPTS s2f@s2f.hamal.nl:html/. >/dev/null && \
    #     sleep 1 && \
        touch README.md 
fi
