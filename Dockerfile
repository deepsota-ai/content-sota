FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DEPLOY_MODE=cloud

# System dependencies: Python, Chrome, Xvfb
RUN apt-get update && apt-get install -y \
    python3.11 python3-pip \
    wget curl gnupg ca-certificates \
    xvfb \
    libx11-6 libxss1 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    fonts-liberation libappindicator3-1 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome stable
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_PATH=/usr/bin/google-chrome-stable

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application source (includes extensions/ibeike/ if present)
COPY . .

# Validate that the iBeike extension was included in the build context.
# If the directory is missing, fail fast with a clear message so the developer
# knows exactly what to do rather than getting a cryptic runtime error.
RUN test -f extensions/ibeike/manifest.json || \
    (echo "" && \
     echo "ERROR: extensions/ibeike/manifest.json not found." && \
     echo "" && \
     echo "To fix: copy the iBeike extension from your local Chrome profile into" && \
     echo "  extensions/ibeike/" && \
     echo "then rebuild the image." && \
     echo "" && \
     echo "Location on Windows:" && \
     echo "  %LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Extensions\\jejejajkcbhejfiocemmddgbkdlhhngm\\<version>\\" && \
     echo "" && \
     exit 1)

# Ensure data directories exist (will be overridden by volume mount in production)
RUN mkdir -p data/publish data/contentGeneration/tip data/coverGeneration

EXPOSE 5001

CMD ["python3", "app.py"]
