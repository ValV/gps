# Use ValV's ESA SNAP as a base image
FROM ubuntu:18.04

WORKDIR "/root"

COPY service .

# Download and install ESA SNAP version 7.0 / raise JVM memory limit up to 4GB
RUN export DEBIAN_FRONTEND=noninteractive && apt update --yes \
    && apt install --yes --no-install-recommends git python3-boto3 python3-pip python3-setuptools python3-wheel software-properties-common \
    && add-apt-repository --yes ppa:ubuntugis/ubuntugis-unstable \
    && apt update --yes \
    && apt install --yes --no-install-recommends python3-gdal=3.0.4+dfsg-1~bionic0 \
    && git clone https://github.com/ValV/b3w.git \
    && pip3 install ./b3w dataclasses marshmallow==3.2.1 pyyaml==5.1.2 shapely==1.6.4 \
    && apt purge --yes --autoremove git python3-pip python3-setuptools python3-wheel software-properties-common \
    && rm -rf b3w /var/lib/apt/lists/*
#    && sed -i -e 's/-Xmx\S\+G/-Xmx12G/g' /usr/local/snap/bin/gpt.vmoptions

# Set entrypoint to Graph Processing Tool executable
ENTRYPOINT ["/usr/bin/python3"]
CMD ["main.py"]
