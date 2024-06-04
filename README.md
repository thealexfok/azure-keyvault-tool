# azure-keyvault-tool
[![Build and Release](https://github.com/thealexfok/azure-keyvault-tool/actions/workflows/release.yml/badge.svg)](https://github.com/thealexfok/azure-keyvault-tool/actions/workflows/release.yml)
Simple script that helps you batch upload secrets and generate a yml file that links your web app environment variable to the key vault.
This program requries python 12.3 or newer
Another GUI is also written in electron but is not maintained

# Run and Build locally
poetry install --with dev
poetry run pyinstaller --onefile --noconsole Azure_kv_tool.py --icon=icon.ico --add-data="icon.ico;."
poetry run pyinstaller Azure_kv_tool.spec