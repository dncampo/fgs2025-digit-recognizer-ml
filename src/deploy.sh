#!/bin/bash

# Exit on error
set -e

# Configuration
APP_NAME="digit-recognizer"
DEPLOY_PATH="/var/www/fgs2025-digit-recognizer-ml"
APACHE_CONF="/etc/apache2/sites-available/${APP_NAME}.conf"
SOURCE_DIR=$(dirname "$(readlink -f "$0")")

echo "=== Starting deployment of ${APP_NAME} ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root"
  exit 1
fi

# Install required packages
echo "=== Installing required packages ==="
apt-get update
apt-get install -y apache2 libapache2-mod-wsgi-py3 python3-pip python3-venv

# Create deployment directory
echo "=== Creating deployment directory ==="
mkdir -p ${DEPLOY_PATH}

# Copy application files
echo "=== Copying application files ==="
cp -r ${SOURCE_DIR}/* ${DEPLOY_PATH}/

# Set up Python virtual environment
echo "=== Setting up Python virtual environment ==="
python3 -m venv ${DEPLOY_PATH}/venv
${DEPLOY_PATH}/venv/bin/pip install -r ${DEPLOY_PATH}/requirements.txt

# Create necessary directories if they don't exist
echo "=== Creating storage directories ==="
for i in {0..9}; do
    mkdir -p ${DEPLOY_PATH}/collected_images/$i
    mkdir -p ${DEPLOY_PATH}/predicted_images/$i
done

# Copy Apache configuration
echo "=== Configuring Apache ==="
cp ${DEPLOY_PATH}/digit-recognizer.conf ${APACHE_CONF}

# Set proper permissions
echo "=== Setting proper permissions ==="
chown -R www-data:www-data ${DEPLOY_PATH}
chmod -R 755 ${DEPLOY_PATH}

# Enable the site and modules
a2ensite ${APP_NAME}
a2enmod wsgi

# Restart Apache
echo "=== Restarting Apache ==="
systemctl restart apache2

echo "=== Deployment complete ==="
echo "Your application should be accessible at http://your-server-ip or http://digit-recognizer.example.com"
echo "Don't forget to update the ServerName in the Apache configuration if needed" 