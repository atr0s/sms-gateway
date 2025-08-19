#!/bin/bash

# Exit on any error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Install system dependencies
apt-get update
apt-get install -y python3 python3-pip python3-venv

# Create sms-gateway user and group if they don't exist
if ! getent group sms-gateway >/dev/null; then
    groupadd -r sms-gateway
fi
if ! getent passwd sms-gateway >/dev/null; then
    useradd -r -g sms-gateway -s /sbin/nologin -d /usr/local/share/sms-gateway sms-gateway
fi

# Create necessary directories
mkdir -p /usr/local/share/sms-gateway
mkdir -p /etc/sms-gateway

# Create virtual environment
VENV_PATH="/usr/local/share/sms-gateway/venv"
python3 -m venv "$VENV_PATH"

# Install dependencies
"$VENV_PATH/bin/pip" install -r requirements.txt

# Copy package files
cp -r sms_gateway /usr/local/share/sms-gateway/
chown -R sms-gateway:sms-gateway /usr/local/share/sms-gateway/sms_gateway

# Create wrapper script for executing the daemon
cat > /usr/local/bin/sms-gateway << 'EOF'
#!/bin/bash
export PYTHONPATH=/usr/local/share/sms-gateway:$PYTHONPATH
exec /usr/local/share/sms-gateway/venv/bin/python -m sms_gateway.daemon "$@"
EOF
chmod +x /usr/local/bin/sms-gateway

# Copy service file
cp deploy/systemd/sms-gateway.service /etc/systemd/system/

# Set permissions
chown -R sms-gateway:sms-gateway /usr/local/share/sms-gateway
chown -R sms-gateway:sms-gateway /etc/sms-gateway
chown root:root /usr/local/bin/sms-gateway
chmod 750 /usr/local/share/sms-gateway
chmod 750 /etc/sms-gateway
chmod 755 /usr/local/bin/sms-gateway

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable sms-gateway.service

echo "SMS Gateway service has been installed."
echo "Please:"
echo "1. Add your configuration file to /etc/sms-gateway/config.json"
echo "2. Start the service with: systemctl start sms-gateway"
echo "3. Check status with: systemctl status sms-gateway"