const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

const toastQueue = [];

function showToast(message) {
  if (toastQueue.length >= 2) {
    return; // If there are already 2 messages in the queue, do not show new message
  }

  const toast = M.toast({ html: message });
  toastQueue.push(toast);

  // Clear the oldest toast after 0.5 seconds
  setTimeout(() => {
    const removedToast = toastQueue.shift();
    removedToast.dismiss();
  }, 500);
}

document.addEventListener('DOMContentLoaded', () => {
  const darkModeToggle = document.getElementById('darkModeToggle');
  
  // Check for saved user preference
  const darkModeEnabled = localStorage.getItem('darkModeEnabled') === 'true';
  document.body.classList.toggle('dark-mode', darkModeEnabled);
  darkModeToggle.checked = darkModeEnabled;
  
  darkModeToggle.addEventListener('change', () => {
    const isEnabled = darkModeToggle.checked;
    document.body.classList.toggle('dark-mode', isEnabled);
    localStorage.setItem('darkModeEnabled', isEnabled);
    showToast(`Dark Mode ${isEnabled ? 'Enabled' : 'Disabled'}`);
  });
});

document.getElementById('clearButton').addEventListener('click', () => {
  document.getElementById('keyVaultNameInput').value = '';
  document.getElementById('envPreview').value = '';
  showToast('Cleared');
});

document.getElementById('uploadInput').addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (file) {
    processEnvFile(file.path);
    const filePathInput = document.querySelector('.file-path');
    filePathInput.value = file.name;
  }
});

document.getElementById('runButton').addEventListener('click', () => {
  const keyVaultName = document.getElementById('keyVaultNameInput').value.trim();
  if (!keyVaultName) {
    showToast('Please enter the Key Vault name.');
    return;
  }
  const envVars = parseEnvPreview(document.getElementById('envPreview').value);
  if (Object.keys(envVars).length === 0) {
    showToast('No environment variables to upload.');
    return;
  }

  window.electron.send('set-secrets', { keyVaultName, envVars });
});

function processEnvFile(filePath) {
  const envVars = readEnvFile(filePath);
  const envPreview = document.getElementById('envPreview');
  envPreview.value = '';
  for (const [key, value] of Object.entries(envVars)) {
    envPreview.value += `${key}: ${value}\n`;
  }
}

function readEnvFile(filePath) {
  const envContent = fs.readFileSync(filePath, 'utf8');
  const envVars = dotenv.parse(envContent);
  const formattedEnvVars = {};
  for (const [key, value] of Object.entries(envVars)) {
    const formattedKey = key.replace(/_/g, '-').replace(/\s/g, '');
    const formattedValue = value.replace(/\s/g, '');
    formattedEnvVars[formattedKey] = formattedValue;
  }
  return formattedEnvVars;
}

function parseEnvPreview(envPreview) {
  const envVars = {};
  const lines = envPreview.split('\n');
  for (const line of lines) {
    if (line.trim() && !line.startsWith('#')) {
      const [key, value] = line.split(':').map(part => part.trim());
      if (key && value) {
        envVars[key] = value;
      }
    }
  }
  return envVars;
}

window.electron.receive('set-secrets-response', (message) => {
  showToast(message);
});
