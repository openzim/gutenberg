FROM python:3.13.2-bookworm

# Install necessary packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      locales \
 && rm -rf /var/lib/apt/lists/* \
 && python -m pip install --no-cache-dir -U \
      pip \
 && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
 && locale-gen "en_US.UTF-8"

# Copy code + associated artifacts
COPY src /src/src
COPY pyproject.toml *.md *.rst get_js_deps.sh LICENSE *.py /src/

# Install + cleanup
RUN pip install --no-cache-dir /src \
 && rm -rf /src

# default output directory
RUN mkdir -p /output
WORKDIR /output

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

CMD ["gutenberg2zim", "--help"]
