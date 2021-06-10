FROM ubuntu:bionic


# Install necessary packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends advancecomp python3-pip python3-dev python3-setuptools libxml2-dev libxslt-dev p7zip-full python3-pillow curl zip bash sed rsync libjpeg-dev libpng-dev wget build-essential make locales && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# add zimwriterfs
RUN wget -L http://download.openzim.org/release/zim-tools/zim-tools_linux-x86_64-2.1.0-1.tar.gz \
    && tar xf zim-tools_linux-x86_64-2.1.0-1.tar.gz \
    && mv zim-tools_linux-x86_64-2.1.0-1/zim* /usr/bin/ \
    && rmdir zim-tools_linux-x86_64-2.1.0-1
RUN zimwriterfs --version

# Install jpegoptim
RUN wget http://www.kokkonen.net/tjko/src/jpegoptim-1.4.4.tar.gz
RUN tar xvf jpegoptim-1.4.4.tar.gz
RUN cd jpegoptim-1.4.4 && ./configure
RUN cd jpegoptim-1.4.4 && make all install

# Install pngquant
RUN wget http://pngquant.org/pngquant-2.9.0-src.tar.gz
RUN tar xvf pngquant-2.9.0-src.tar.gz
RUN cd pngquant-2.9.0 && ./configure
RUN cd pngquant-2.9.0 && make all install

# Install gifsicle
RUN wget https://www.lcdf.org/gifsicle/gifsicle-1.88.tar.gz
RUN tar xvf gifsicle-1.88.tar.gz
RUN cd gifsicle-1.88 && ./configure
RUN cd gifsicle-1.88 && make all install

# Install gutenberg (from source)
RUN locale-gen "en_US.UTF-8"
COPY requirements.pip /src/
RUN python3 -m pip install -r /src/requirements.pip
COPY LICENSE /src/
COPY pypi-readme.rst /src/
COPY languages_06_2018 /src/
COPY MANIFEST.in /src/
COPY setup.py /src/
COPY gutenberg2zim /src/
COPY gutenbergtozim /src/gutenbergtozim
WORKDIR /src/
RUN python3 ./setup.py install

# Boot commands
WORKDIR /output

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
CMD gutenberg2zim --help ; /bin/bash
