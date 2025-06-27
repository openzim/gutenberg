#build frontend
FROM node:20-alpine AS zimui

WORKDIR /src
COPY zimui /src
RUN yarn install --frozen-lockfile
RUN yarn build

# Backend base
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

# Copy global files
COPY README.md scraper/pyproject.toml /src/scraper/
COPY README.md scraper/

# Copy code + associated artifacts
COPY scraper/src /src/scraper/src



# Install + cleanup
RUN pip install --no-cache-dir /src/scraper \
 && rm -rf /src/scraper

# Copy zimui build output
COPY --from=zimui /src/dist /src/zimui

ENV GUTENBURG_ZIMUI_DIST=/src/zimui

WORKDIR /output
CMD ["gutenberg2zim", "--help"]
