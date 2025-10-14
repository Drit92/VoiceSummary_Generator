#!/bin/bash


pip install --upgrade pip


pip install --no-cache-dir --no-binary :all: -r requirements.txt


mkdir -p ~/.streamlit/

# Streamlit server configuration
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
