#!/bin/bash

# Upgrade pip to the latest version
pip install --upgrade pip

# Install dependencies from requirements.txt without cache or building from source
pip install --no-cache-dir --no-binary :all: -r requirements.txt

# Create the Streamlit config directory (if it doesn't exist)
mkdir -p ~/.streamlit/

# Streamlit server configuration
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
