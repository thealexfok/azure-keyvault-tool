const fs = require('fs');
const dotenv = require('dotenv');
const { SecretClient } = require('@azure/keyvault-secrets');
const { DefaultAzureCredential } = require('@azure/identity');

function readEnvFile(filePath) {
  const envVars = {};
  const fileContent = fs.readFileSync(filePath, 'utf8');
  const lines = fileContent.split('\n');
  lines.forEach(line => {
    if (line.trim() && !line.startsWith('#')) {
      const [key, value] = line.trim().split('=', 2);
      if (key && value) {
        envVars[key.replace(/_/g, '-').replace(/\s/g, '')] = value.replace(/\s/g, '');
      }
    }
  });
  return envVars;
}

async function setSecrets(keyVaultName, envVars) {
  const credential = new DefaultAzureCredential();
  const client = new SecretClient(`https://${keyVaultName}.vault.azure.net`, credential);
  for (const [key, value] of Object.entries(envVars)) {
    await client.setSecret(key, value);
  }
}

function saveToYaml(keyVaultName, envVars, yamlFilePath) {
  const yamlContent = `
parameters:
  - name: environment
    type: string

stages:
- stage: Update_Environment_Variables
  displayName: Update Environment Variables
  jobs:
  - job: Update_Environment_Variables
    displayName: Update Environment Variables
    steps:
    - task: AzureCLI@2
      displayName: 'Update environment variables'
      inputs:
        azureSubscription: $(azureSubscription)
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          az webapp config appsettings set --resource-group $(resource_group_name) --name $(web_app_name) --settings \\
${Object.entries(envVars).map(([key, value]) => `          ${key.replace(/-/g, '_')}="@Microsoft.KeyVault(SecretUri=https://${keyVaultName}\${{ parameters.environment }}.vault.azure.net/secrets/${key}/)"`).join('\n')}
  `;

  fs.writeFileSync(yamlFilePath, yamlContent.trim());
}

module.exports = {
  readEnvFile,
  setSecrets,
  saveToYaml
};
