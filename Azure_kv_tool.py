__author__ = "Alex Fok"
__copyright__ = "Copyright (©) 2024 Alex Fok"
__credits__ = ["Alex Fok"]
__license__ = "GPL"
__version__ = "1.0"
__email__ = "thisisalexfok@gmail.com"


import os
import sys
import yaml
import json
import threading
import subprocess

# Azure
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# GUI
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, QWidget, QLineEdit, QMessageBox)
from PyQt6.QtGui import (QDragEnterEvent, QDropEvent,QIcon)
from PyQt6.QtCore import (Qt, pyqtSignal, pyqtSlot)

basedir = os.path.dirname(__file__)

try:
    from ctypes import windll  # Windows.
    myappid = 'thalexfok.keyvaulttool'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

class KeyVaultUploader(QMainWindow):
    login_status_signal = pyqtSignal(str)
    subscriptions_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Azure Key Vault Secrets Tool")
        self.setGeometry(100, 100, 1080, 720)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.login_status = QLabel("Checking login status...", self)
        self.login_status.setStyleSheet("color: blue;")
        self.layout.addWidget(self.login_status)

        self.login_button = QPushButton("Login to Azure CLI", self)
        self.login_button.clicked.connect(self.login_to_azure)
        self.layout.addWidget(self.login_button)

        self.subscriptions_label = QLabel("Your Subscriptions and Key Vaults:", self)
        self.layout.addWidget(self.subscriptions_label)

        self.subscriptions_list = QTextEdit(self)
        self.subscriptions_list.setReadOnly(True)
        self.layout.addWidget(self.subscriptions_list)

        self.key_vault_label = QLabel("Enter Key Vault Name:", self)
        self.layout.addWidget(self.key_vault_label)

        self.key_vault_input = QLineEdit(self)
        self.layout.addWidget(self.key_vault_input)

        self.setAcceptDrops(True)
        self.drag_button = QPushButton("Drag and drop .env file here or click here to upload", self)
        self.drag_button.setAcceptDrops(True)
        self.drag_button.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.drag_button)

        self.env_preview_label = QLabel("Environment Variables Preview:", self)
        self.layout.addWidget(self.env_preview_label)

        self.env_preview = QTextEdit(self)
        self.env_preview.setReadOnly(True)
        self.layout.addWidget(self.env_preview)

        self.run_button = QPushButton("Run", self)
        self.run_button.clicked.connect(self.set_variables)
        self.layout.addWidget(self.run_button)

        self.clear_button = QPushButton("Clear", self)
        self.clear_button.clicked.connect(self.clear_preview)
        self.layout.addWidget(self.clear_button)

        self.save_button = QPushButton("Save YAML", self)
        self.save_button.clicked.connect(self.save_yaml)
        self.layout.addWidget(self.save_button)

        self.env_vars = {}

        self.login_status_signal.connect(self.update_login_status)
        self.subscriptions_signal.connect(self.update_subscriptions)

        # Check login status on startup in a separate thread
        threading.Thread(target=self.check_login_status).start()

    @pyqtSlot(str)
    def update_login_status(self, status):
        self.login_status.setText(status)

    @pyqtSlot(str)
    def update_subscriptions(self, subscriptions):
        self.subscriptions_list.setText(subscriptions)
        

    def check_login_status(self):
        self.subscriptions_signal.emit("Not logged in")
        result = subprocess.run("az account show --output json > az_account.json", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        result = result.returncode
        if result == 0:
            with open("az_account.json") as f:
                account_info = json.load(f)
                email = account_info["user"]["name"]
                self.login_status_signal.emit(f"Logged in as {email}")
            os.remove("az_account.json")
            self.get_subscriptions()
        else:
            self.login_status_signal.emit("Not logged in")

    def login_to_azure(self):
        result = subprocess.run("az login --output json > az_login.json", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        result = result.returncode
        if result == 0:
            with open("az_login.json") as f:
                login_info = json.load(f)
                email = login_info[0]["user"]["name"]
                self.login_status_signal.emit(f"Logged in as {email}")
            os.remove("az_login.json")
            self.get_subscriptions()
        else:
            self.login_status_signal.emit("Failed to login to Azure CLI")

    def get_subscriptions(self):
        self.subscriptions_signal.emit("Fetching Subscriptions...")
        result = subprocess.run("az account list --output json > az_subscriptions.json", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        result = result.returncode
        if result == 0:
            with open("az_subscriptions.json") as f:
                subscriptions_info = json.load(f)
                subscriptions_text = ""
                for sub in subscriptions_info:
                    sub_id = sub["id"]
                    sub_name = sub["name"]
                    subscriptions_text += f"{sub_name}:\n"
                    key_vaults = self.get_key_vaults(sub_id)
                    for kv in key_vaults:
                        subscriptions_text += f"  - {kv}\n"
                self.subscriptions_signal.emit(subscriptions_text)
            os.remove("az_subscriptions.json")
        else:
            self.subscriptions_signal.emit("Failed to retrieve subscriptions")

    def get_key_vaults(self, subscription_id):
        self.subscriptions_signal.emit("Fetching Key Vaults...")
        subprocess.run(f"az account set --subscription {subscription_id}", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run("az keyvault list --output json > az_keyvaults.json", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        with open("az_keyvaults.json") as f:
            key_vaults_info = json.load(f)
            key_vaults = [kv["name"] for kv in key_vaults_info]
        os.remove("az_keyvaults.json")
        return key_vaults

    def initUI(self):
        self.setWindowTitle('Azure Key Vault Secrets Upload Tool')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.key_vault_name_input = QLineEdit(self)
        self.key_vault_name_input.setPlaceholderText('Enter Key Vault Name')
        layout.addWidget(self.key_vault_name_input)

        self.upload_button = QPushButton('Select a .env File', self)
        self.upload_button.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.upload_button)

        self.clear_button = QPushButton('Clear environment file', self)
        self.clear_button.clicked.connect(self.clear_env_file)
        layout.addWidget(self.clear_button)

        self.preview_label = QLabel('Environment Variables Preview:')
        layout.addWidget(self.preview_label)

        self.env_preview = QTextEdit(self)
        self.env_preview.setReadOnly(True)
        layout.addWidget(self.env_preview)

        self.run_button = QPushButton('Run', self)
        self.run_button.clicked.connect(self.set_variables)
        layout.addWidget(self.run_button)

        self.setLayout(layout)

        self.setAcceptDrops(True)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Open .env file", "", "All Files (*);;Text Files (*.txt);;Env Files (*.env)", options=options)
        if file_name:
            self.load_env_file(file_name)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("background-color: lightgreen;")
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        for url in event.mimeData().urls():
            file_name = url.toLocalFile()
            self.load_env_file(file_name)
    
    def preview_env_vars(self):
        preview_text = "\n".join([f"{key}: {value}" for key, value in self.env_vars.items()])
        self.env_preview.setText(preview_text)
    
    def clear_preview(self):
        self.env_vars.clear()
        self.env_preview.clear()
    
    def load_env_file(self, file_name):
        with open(file_name, 'r') as file:
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    self.env_vars[key.strip()] = value.strip().replace(" ", "")
            self.preview_env_vars()

    def clear_env_file(self):
        self.env_file_path = ""
        self.env_vars = {}
        self.env_preview.clear()

    def process_env_file(self):
        self.env_vars = read_env_file(self.env_file_path)
        self.env_preview.clear()
        for key, value in self.env_vars.items():
            self.env_preview.append(f"{key}: {value}")

    def load_env_file(self, file_name):
        with open(file_name, 'r') as file:
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    self.env_vars[key.strip()] = value.strip().replace(" ", "")
            self.preview_env_vars()

    def preview_env_vars(self):
        preview_text = "\n".join([f"{key}: {value}" for key, value in self.env_vars.items()])
        self.env_preview.setText(preview_text)
    
    def clear_preview(self):
        self.env_vars.clear()
        self.env_preview.clear()

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

    def save_yaml(self):
        key_vault_name = self.key_vault_input.text()
        if not key_vault_name:
            QMessageBox.warning(self, "Input Error", "Please enter the Key Vault name.")
            return
        
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save YAML File", "env.yml", "YAML Files (*.yml);;All Files (*)", options=options)
        
        if not file_name:
            return
        
        if not file_name.endswith('.yml'):
            file_name += '.yml'
        
        self.save_to_yaml(key_vault_name, self.env_vars, file_name)
        QMessageBox.information(self, "Success", "YAML file saved successfully.")

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



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(basedir, 'icon.ico')))
    uploader = KeyVaultUploader()
    uploader.show()
    sys.exit(app.exec())
