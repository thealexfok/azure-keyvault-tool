# Azure Key vault tool
[![Build and Release](https://github.com/thealexfok/azure-keyvault-tool/actions/workflows/release.yml/badge.svg)](https://github.com/thealexfok/azure-keyvault-tool/actions/workflows/release.yml)<a href="#Contributing"><img src="https://img.shields.io/badge/Pull_Requests-Welcome-brightgreen.svg" alt="Pull Requests Welcome"></a>

Simple script that helps you batch upload secrets and generate a yml file.

The yml file could then be used in your pipeline to update your web app settings which reference your web app environment variable to the key vault.
This script requries python 12.3 or newer.

Another GUI was written in electron under the folder /electron but is not maintained.



# Run locally 
`poetry install`
`poetry run Azure_kv_tool.py`



# Build locally

`poetry install --with dev`

`poetry run pyinstaller --onefile --noconsole Azure_kv_tool.py --icon=icon.ico --add-data="icon.ico;."`
`poetry run pyinstaller Azure_kv_tool.spec`



## Contributing

Feel free to submit a pull request if you would like to contribute.



## Issues

[Open a new issue](https://github.com/thealexfok/azure-keyvault-tool/issues/new/choose)



## License

This project is open source under GPLv3.