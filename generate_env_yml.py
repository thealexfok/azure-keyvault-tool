__author__ = "Alex Fok"
__copyright__ = "Copyright (©) 2024 Alex Fok"
__credits__ = ["Alex Fok"]
__license__ = "GPL"
__version__ = "1.0"
__email__ = "thisisalexfok@gmail.com"

import os
import sys
import yaml
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QFileDialog, QTextEdit, QLabel, QMessageBox)
from PyQt5.QtCore import Qt

# Function to read .env file and return a dictionary of environment variables
def read_env_file(file_path):
    env_vars = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                key = key.replace('_', '-').replace(' ', '')  # Replace underscores and remove spaces from keys
                value = value.replace(' ', '')  # Remove spaces from values
                env_vars[key] = value
    return env_vars

# Function to save environment variables to a YAML file
def save_to_yaml(key_vault_name, env_vars, yaml_file_path):
    # Construct the YAML content
    yaml_content = (
        "parameters:\n"
        "  - name: environment\n"
        "    type: string\n"
        "\n"
        "stages:\n"
        "- stage: Update_Environment_Variables\n"
        "  displayName: Update Environment Variables\n"
        "  jobs:\n"
        "  - job: Update_Environment_Variables\n"
        "    displayName: Update Environment Variables\n"
        "    steps:\n"
        "    - task: AzureCLI@2\n"
        "      displayName: 'Update environment variables'\n"
        "      inputs:\n"
        "        azureSubscription: $(azureSubscription)\n"
        "        scriptType: 'bash'\n"
        "        scriptLocation: 'inlineScript'\n"
        "        inlineScript: |\n"
        "          az webapp config appsettings set --resource-group $(resource_group_name) --name $(web_app_name) --settings \\\n"
    )

    # Add each environment variable setting
    for key, value in env_vars.items():
        formatted_key = key.replace('-', '_')
        yaml_content += (
            f"          {formatted_key}=\"@Microsoft.KeyVault(SecretUri=https://{key_vault_name}${{{{ parameters.environment }}}}.vault.azure.net/secrets/{key}/)\"\n"
        )

    # Add the closing YAML content
    yaml_content += (
        "\n"
    )

    # Write the YAML content to the file
    with open(yaml_file_path, 'w') as yaml_file:
        yaml_file.write(yaml_content)



class KeyVaultUploader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.env_vars = {}
        self.env_file_path = ""
        self.key_vault_name = ""

    def initUI(self):
        self.setWindowTitle('Azure Key Vault Secret Upload Tool')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.key_vault_name_input = QLineEdit(self)
        self.key_vault_name_input.setPlaceholderText('Enter Key Vault Name')
        layout.addWidget(self.key_vault_name_input)

        self.upload_label = QLabel('Drag and drop .env file here or click below to upload:')
        layout.addWidget(self.upload_label)

        self.upload_button = QPushButton('Select a .env File', self)
        self.upload_button.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.upload_button)

        self.clear_button = QPushButton('Clear', self)
        self.clear_button.clicked.connect(self.clear_env_file)
        layout.addWidget(self.clear_button)

        self.preview_label = QLabel('Preview:')
        layout.addWidget(self.preview_label)

        self.env_preview = QTextEdit(self)
        self.env_preview.setReadOnly(True)
        layout.addWidget(self.env_preview)

        self.run_button = QPushButton('Run', self)
        self.run_button.clicked.connect(self.set_variables)
        layout.addWidget(self.run_button)

        self.setLayout(layout)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("background-color: lightgreen;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event):
        self.setStyleSheet("")
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.env_file_path = files[0]
            self.process_env_file()

    def open_file_dialog(self):
        self.env_file_path, _ = QFileDialog.getOpenFileName(self, "Select .env file", "", "Environment Files (*.env)")
        if self.env_file_path:
            self.process_env_file()

    def clear_env_file(self):
        self.env_file_path = ""
        self.env_vars = {}
        self.env_preview.clear()

    def process_env_file(self):
        self.env_vars = read_env_file(self.env_file_path)
        self.env_preview.clear()
        for key, value in self.env_vars.items():
            self.env_preview.append(f"{key}: {value}")

    def set_variables(self):
        self.key_vault_name = self.key_vault_name_input.text().strip()
        if not self.key_vault_name:
            QMessageBox.warning(self, "Input Error", "Please enter the Key Vault name.")
            return
        if not self.env_vars:
            QMessageBox.warning(self, "Input Error", "No environment variables to upload.")
            return

        key_vault_url = f"https://{self.key_vault_name}.vault.azure.net"

        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=key_vault_url, credential=credential)

            print(f"Connected to Key Vault {self.key_vault_name}")

            for key, value in self.env_vars.items():
                print(f"Setting secret '{key}' in Key Vault {self.key_vault_name}...")
                client.set_secret(key, value)
                print(f"Success: Set secret '{key}' in Key Vault {self.key_vault_name}")
            
            default_yaml_path = os.path.join(os.path.dirname(self.env_file_path), "env.yml")
            yaml_file_path, _ = QFileDialog.getSaveFileName(self, "Save YAML file", default_yaml_path, "YAML Files (*.yml)")
            if yaml_file_path:
                save_to_yaml(self.key_vault_name, self.env_vars, yaml_file_path)
                QMessageBox.information(self, "Success", f"Environment variables have been set in Key Vault and {yaml_file_path} has been generated.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set secrets in Key Vault: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    uploader = KeyVaultUploader()
    uploader.show()
    sys.exit(app.exec_())
