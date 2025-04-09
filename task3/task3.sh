#!/bin/bash

# Load environment variables
source .env 

# Ensure required environment variables are set
for var in SAT_PROFILE_NAME SAT_DATABRICKS_WORKSPACE_URL SAT_SP_CLIENT SAT_SP_SECRET; do
  if [ -z "${!var}" ]; then
    echo "❌ Missing environment variable: $var"
    exit 1
  fi
done

# Install Databricks CLI
echo "🔍 Checking for Databricks CLI v2..."
if ! command -v databricks &> /dev/null || ! databricks -v | grep -q "Databricks CLI v0.2"; then
  echo "📦 Installing Databricks CLI v2..."
  curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sudo sh
  echo "✅ Databricks CLI installed: $(databricks -v)"
else
  echo "✅ Databricks CLI v2 already installed: $(databricks -v)"
fi

# Configure profile for SP
echo "📁 Configuring profile [$SAT_PROFILE_NAME]..."
CONFIG_FILE="$HOME/.databrickscfg"
if grep -q "^\[$SAT_PROFILE_NAME\]" "$CONFIG_FILE"; then
  echo "Profile $SAT_PROFILE_NAME already exists. Skipping..."
else
  cat <<EOF >> "$CONFIG_FILE"

[${SAT_PROFILE_NAME}]
host          = ${SAT_DATABRICKS_WORKSPACE_URL}
client_id     = ${SAT_SP_CLIENT} 
client_secret = ${SAT_SP_SECRET}
EOF

  echo "✅ Profile [$SAT_PROFILE_NAME] added successfully."
fi


# Clone SAT repo and install
echo "Cloning SAT..."
# git clone https://github.com/databricks-industry-solutions/security-analysis-tool.git
git clone --branch add-env-vars https://github.com/joyaung/security-analysis-tool.git # Includes my edits to code base
cd security-analysis-tool
chmod +x install.sh
./install.sh
