# vim:set ft=dockerfile:
FROM alpine:3.14
ENV PYTHONUNBUFFERED=1

MAINTAINER "Rob Wolfram <stock2flow@hamal.nl>"

RUN echo "**** install Python ****" && \
    apk add --no-cache python3 py3-pip py3-setuptools && \
    [ -e /usr/bin/python ] || ln -sf python3 /usr/bin/python && \
    [ -e /usr/bin/pip ] || ln -sf pip3 /usr/bin/pip && \
    apk add --no-cache py3-numpy py3-requests py3-scikit-learn py3-scipy && \
    pip install charset-normalizer && \
    \
    echo "**** install gnuplot ****" && \
    apk add --no-cache gnuplot ttf-freefont \
        fontconfig msttcorefonts-installer && \
    update-ms-fonts && \
    fc-cache -f && \
    rm -rf /var/cache/apk/* && \
    \
    echo "**** install dcron ****" && \
    apk add --no-cache dcron curl git && \
    \
    echo "**** install ssh, imagemagick ****" && \
    apk add --no-cache openssh-client ca-certificates imagemagick make && \
    \
    mkdir -p /data

VOLUME /data

COPY cronstarter.sh /

CMD ["/cronstarter.sh"]

