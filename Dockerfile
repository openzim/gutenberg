FROM node:20-alpine as ui

WORKDIR /src
COPY ui /src
RUN yarn install --frozen-lockfile || npm install
RUN yarn build || npm run build

FROM python:3.13.2-bookworm

LABEL org.opencontainers.image.source https://github.com/openzim/gutenberg

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
COPY scraper/pyproject.toml scraper/get_js_deps.sh scraper/hatch_build.py /scraper/
COPY scraper/src/gutenberg2zim/__about__.py /scraper/src/gutenberg2zim/__about__.py
COPY scraper/src/gutenberg2zim/templates /scraper/src/gutenberg2zim/templates

# Install only dependencies
RUN pip install --no-cache-dir /scraper 

# Copy code + remaining artifacts
ENV LOCALES_LOCATION /locales
COPY locales /locales
COPY *.md *.rst LICENSE /scraper/
COPY scraper /scraper

# Install + cleanup
RUN pip install --no-cache-dir /scraper \
 && rm -rf /scraper

# Copy Vue.js UI build output
COPY --from=ui /src/dist /src/ui

ENV GUTENBERG_UI_DIST=/src/ui

# default output directory
RUN mkdir -p /output
WORKDIR /output

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    GUTENBERG_OUTPUT=/output

CMD ["gutenberg2zim", "--help"]
