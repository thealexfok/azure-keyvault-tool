# azure-keyvault-tool
Simple script that helps you batch upload secrets and generate a yml file that links your web app environment variable to the key vault

# Run and Build locally
poetry install --with dev
poetry run pyinstaller --onefile --noconsole Azure_kv_tool.py --icon=icon.ico --add-data="icon.ico;."
poetry run pyinstaller Azure_kv_tool.spec