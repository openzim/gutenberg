FROM node:20-alpine as zimui

WORKDIR /src
COPY zimui /src
RUN yarn install --frozen-lockfile
RUN yarn build
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
COPY pyproject.toml *.md *.rst LICENSE *.py /src/

# Copy backend source code
COPY scraper/src /src/scraper/src

# Copy pyproject.toml, openzim.toml, *.sh
COPY scraper/pyproject.toml scraper/openzim.toml /src/scraper/

# Copy markdown / reStructuredText, LICENSE、*.py
COPY README.md *.md *.rst LICENSE scraper/*.py /src/scraper/


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
