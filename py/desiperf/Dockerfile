FROM ubuntu:latest
LABEL maintainer="Parker Fagrelius <parkerf@berkeley.edu>"

# Base Ubuntu packages

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8

RUN \
    apt-get update          &&  \
    apt-get --yes upgrade   &&  \
    apt-get --yes install       \
        bzip2                   \
        curl                    \
        git                     \
        libffi-dev              \
        lsb-release             \
        tzdata                  \
        vim                     \
        wget

# Timezone to Berkeley

ENV TZ=America/Los_Angeles
RUN \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime  &&  \
    echo $TZ > /etc/timezone

# Python 3 Miniconda and dependencies

RUN \
    curl -s -o /tmp/miniconda3.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh &&  \
    bash /tmp/miniconda3.sh -b -p /opt/anaconda3            &&  \
    rm -rf /tmp/miniconda3.sh                               &&  \
    /opt/anaconda3/bin/conda update --yes conda             &&  \
    /opt/anaconda3/bin/conda install --yes                      \
            --channel conda-forge   \
            astropy             \
            bokeh               \
            pandas              \
            numpy               \
            scipy               \ 
            matplotlib

ENV PATH=/opt/anaconda3/bin:$PATH
WORKDIR /srv

ENV XDG_CACHE_HOME=/srv/cache
RUN mkdir -p $XDG_CACHE_HOME/astropy

ENV XDG_CONFIG_HOME=/srv/config
RUN mkdir -p $XDG_CONFIG_HOME/astropy

ADD instperfapp /srv/instperfapp
RUN python3 -c "import astropy"

CMD ["bokeh", "serve", "--show", "instperfapp"]
