# AzureFunctionHealthCheck
This project can be used for creating the Azure Function for Health Check.

## Start from scratch (can be ignored if you download this project from github)
Install:
- https://functionscdn.azureedge.net/public/artifacts/v4/latest/func-cli-x64.msi
- https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
- https://marketplace.visualstudio.com/items?itemName=Azurite.azurite

### Start coding
```
py -m venv .venv
.venv\scripts\activate
func init --python
func templates list
func new --name HealtchCheck01 --template "Timer trigger"
code .
  ```
# Run project locally
- Press F1 and choose ```Azurite: Start```
- Start function locally ```func start --verbose```