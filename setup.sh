#!/bin/bash

# Upgrade pip to the latest version
pip install --upgrade pip

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Other setup commands can go here (if necessary)



mkdir -p ~/.streamlit/


echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml

