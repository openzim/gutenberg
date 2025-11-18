FROM node:20-alpine AS ui

WORKDIR /src
COPY ui /src
RUN yarn install --frozen-lockfile || npm install
RUN yarn build || npm run build

FROM python:3.13.2-bookworm

LABEL org.opencontainers.image.source="https://github.com/openzim/gutenberg"

# Install necessary packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      locales \
 && rm -rf /var/lib/apt/lists/* \
 && python -m pip install --no-cache-dir -U \
      pip \
 && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
 && locale-gen "en_US.UTF-8"

# Copy code + remaining artifacts
ENV LOCALES_LOCATION=/locales
COPY locales /locales
COPY README.md *.rst LICENSE /src/
COPY scraper /src/scraper

# Install package (pip should install dependencies from pyproject.toml automatically)
RUN pip install --no-cache-dir /src/scraper \
 && rm -rf /src/scraper

# Copy Vue.js UI build output
COPY --from=ui /src/dist /src/zimui

ENV GUTENBERG_UI_DIST=/src/zimui

# default output directory
RUN mkdir -p /output
WORKDIR /output

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    GUTENBERG_OUTPUT=/output

CMD ["gutenberg2zim", "--help"]
