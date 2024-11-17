# AzureFunctionHealthCheck
This project can be used for creating the Azure Function for Health Check.
The following can be checked
- ping
- http status
- http string
- ICAP server processing (needs )

## Start from scratch (can be ignored if you download this project from github)
Install:
- https://functionscdn.azureedge.net/public/artifacts/v4/latest/func-cli-x64.msi
- https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
- https://marketplace.visualstudio.com/items?itemName=Azurite.azurite

### Start coding
```
# Navigate to your function app directory
Set-Location -Path AzureFunctionHealthCheck
# Create a virtual environment in the current directory
py -m venv .venv
# Activate the virtual environment
.venv\scripts\activate
# Initialize a new Azure Functions project with Python
func init --python

# List available function templates
func templates list

# Create a new function named "HealthCheck01" using the "Timer trigger" template
func new --name HealthCheck01 --template "Timer trigger"

# Open the project in Visual Studio Code
code .
  ```
# Run project locally
- Press F1 and choose ```Azurite: Start```
- Install dependencies ```pip install -r requirements.txt```
- Start function locally ```func start --verbose```
# Publish Function To Azure (To avoid transfering unnessesary files do the deployment after checkout/clone the reposiy - not after running locally)
```
# Navigate to your function app directory
Set-Location -Path AzureFunctionHealthCheck

# Create a ZIP file of the function app directory
Compress-Archive -Path * -DestinationPath function_app.zip -Force

# Display zip contents
$tempDir = New-Item -ItemType Directory -Path "$env:TEMP\function_app_temp"
Expand-Archive -Path function_app.zip -DestinationPath $tempDir
Get-ChildItem -Path $tempDir -Recurse
Remove-Item -Path $tempDir -Recurse

# Deploy the ZIP file to Azure Function App using Azure CLI
az login
az account show
az account set --subscription <subscription-id>
az functionapp deployment source config-zip --resource-group MyResourceGroup --name MyFunctionApp --src function_app.zip
 az webapp log deployment show -n MyResourceGroup -g MyFunctionApp
```
