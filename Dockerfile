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

# Copy pyproject.toml and its dependencies
COPY pyproject.toml README.md get_js_deps.sh hatch_build.py /scraper/
COPY src/gutenberg2zim/__about__.py /scraper/src/gutenberg2zim/__about__.py
COPY src/gutenberg2zim/templates /scraper/src/gutenberg2zim/templates

# Install only dependencies
RUN pip install --no-cache-dir /scraper 

# Copy code + remaining artifacts
ENV LOCALES_LOCATION /locales
COPY locales /locales
COPY *.md *.rst get_js_deps.sh LICENSE *.py /scraper/
COPY src /scraper/src

# Install + cleanup
RUN pip install --no-cache-dir /scraper \
 && rm -rf /scraper

# default output directory
RUN mkdir -p /output
WORKDIR /output

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    GUTENBERG_OUTPUT=/output

CMD ["gutenberg2zim", "--help"]
