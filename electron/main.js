const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const backend = require('./backend'); // Ensure this path is correct based on your project structure

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'), // Use preload script for better security
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  win.loadFile('index.html');
  // Remove the line that opens the developer tools by default
  // win.webContents.openDevTools(); // Comment or remove this line to prevent dev tools from opening
}

// Create an empty menu to remove the default menu
const menu = Menu.buildFromTemplate([]);
Menu.setApplicationMenu(menu);

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

ipcMain.on('set-secrets', async (event, { keyVaultName, envVars }) => {
  try {
    await backend.setSecrets(keyVaultName, envVars);
    const yamlFilePath = path.join(app.getPath('documents'), 'env.yml');
    await backend.saveToYaml(keyVaultName, envVars, yamlFilePath);
    event.reply('set-secrets-response', `Environment variables have been set in Key Vault and ${yamlFilePath} has been generated.`);
  } catch (error) {
    event.reply('set-secrets-response', `Failed to set secrets in Key Vault: ${error.message}`);
  }
});
