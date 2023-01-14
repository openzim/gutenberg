FROM python:3.11.1-bullseye

# Install necessary packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends advancecomp libxml2-dev libxslt-dev python3-pillow rsync libjpeg-dev libpng-dev libmagic1 locales jpegoptim pngquant gifsicle && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

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
