#build frontend
FROM node:20-alpine as zimui

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

# Set workdir
WORKDIR /src

# Copy code + associated artifacts
COPY scraper/src /src/scraper/src
COPY scraper/*.py /src/scraper/
COPY scraper/pyproject.toml /src/scraper/

# Copy global files
COPY README.md LICENSE pyproject.toml /src/


# Install + cleanup
RUN pip install --no-cache-dir /src/scraper \
 && rm -rf /src/scraper

# default output directory
RUN mkdir -p /output
WORKDIR /output

# Copy zimui build output
COPY --from=zimui /src/dist /src/zimui

ENV GUTENBURG_ZIMUI_DIST=/src/zimui

CMD ["gutenberg2zim", "--help"]
