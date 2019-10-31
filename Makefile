SHELL=/bin/bash
PATH=/bin:/usr/bin

all: README.md

README.md: s2fcharts.html alltimeprice.svg detailprice.svg stock2flow.svg
	@source ./bashvar.sh && \
	    sed -i -e "s/--DT-->.*<!/--DT-->$(date -d @$SFDT +%F)<!/" \
	    -e "s/--CP-->.*<!/--CP-->\$$SFCP<!/" \
	    -e "s/--PP-->.*<!/--PP-->\$$SFPP<!/" \
	    -e "s/--PP1-->.*<!/--PP1-->\$$SFPP1<!/" \
	    -e "s/--PM1-->.*<!/--PM1-->\$$SFPM1<!/" \
	    -e "s/--PP2-->.*<!/--PP2-->\$$SFPP2<!/" \
	    -e "s/--PM2-->.*<!/--PM2-->\$$SFPM2<!/" \
	    s2fcharts.html && \
	    sftp -q s2f@s2f.hamal.nl:html/images/. <<< $$'put *.svg' >/dev/null && \
	    sftp -q s2f@s2f.hamal.nl:html/. <<< $$'put s2fcharts.html' >/dev/null && \
	    touch README.md 

s2fcharts.html alltimeprice.svg detailprice.svg stock2flow.svg: bashvar.sh sfdata.csv sftime.csv gpvars.txt
	@gnuplot stock2flowcharts.gpl 2>/dev/null

gpvars.txt: FORCE
	@source ~/lib/python/scikit/bin/activate && \
	    python gens2fdata.py --quiet

FORCE: ;

clean:
	@rm alltimeprice.svg detailprice.svg stock2flow.svg bashvar.sh sfdata.csv sftime.csv gpvars.txt

.PHONY: all
