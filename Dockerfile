FROM node:24-alpine AS ui

WORKDIR /src/ui
COPY locales /src/locales
COPY ui /src/ui
COPY scraper/src/gutenberg2zim /src/scraper/src/gutenberg2zim
RUN yarn install --frozen-lockfile || npm install
RUN yarn build || npm run build

FROM python:3.14-bookworm

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

# Copy pyproject.toml and its dependencies
COPY README.md LICENSE /src/
COPY scraper/pyproject.toml /src/scraper/
COPY scraper/src/gutenberg2zim/__about__.py /src/scraper/src/gutenberg2zim/__about__.py

# Install Python dependencies
RUN pip install --no-cache-dir /src/scraper

# Copy code + remaining artifacts
ENV LOCALES_LOCATION=/locales
COPY locales /locales
COPY scraper /src/scraper

# Copy the UI build into the scraper package before installing it.
COPY --from=ui /src/scraper/src/gutenberg2zim/zimui /src/scraper/src/gutenberg2zim/zimui

# Install scraper itself + cleanup
RUN pip install --no-cache-dir /src/scraper \
 && rm -rf /src/scraper

# default output directory
RUN mkdir -p /output
WORKDIR /output

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    ZIM_OUTPUT=/output

CMD ["gutenberg2zim", "--help"]
