# Installation paths
PREFIX ?= /usr/local
SYSCONFDIR ?= /etc
PYTHON ?= python3

# Service name
SERVICE_NAME = sms-gateway

# Installation directories
INSTALL_BIN = $(PREFIX)/bin
INSTALL_SHARE = $(PREFIX)/share/$(SERVICE_NAME)
INSTALL_CONF = $(SYSCONFDIR)/$(SERVICE_NAME)
SYSTEMD_DIR = /etc/systemd/system

.PHONY: help install uninstall

help:
	@echo "Available targets:"
	@echo "  help     - Show this help message"
	@echo "  install  - Install the SMS Gateway service"
	@echo "  uninstall - Remove the SMS Gateway service"

install:
	@echo "Installing SMS Gateway..."
	
	# Check for root permissions
	@if [ "$$(id -u)" != "0" ]; then \
		echo "This target must be run as root" >&2; \
		exit 1; \
	fi

	# Create user and group
	@if ! getent group $(SERVICE_NAME) >/dev/null; then \
		groupadd -r $(SERVICE_NAME); \
	fi
	@if ! getent passwd $(SERVICE_NAME) >/dev/null; then \
		useradd -r -g $(SERVICE_NAME) -s /sbin/nologin -d $(INSTALL_SHARE) $(SERVICE_NAME); \
	fi

	# Create directories
	install -d $(INSTALL_SHARE)
	install -d $(INSTALL_CONF)

	# Create and setup virtualenv
	$(PYTHON) -m venv $(INSTALL_SHARE)/venv
	$(INSTALL_SHARE)/venv/bin/pip install -r requirements.txt

	# Copy package files
	cp -r sms_gateway $(INSTALL_SHARE)/
	chown -R $(SERVICE_NAME):$(SERVICE_NAME) $(INSTALL_SHARE)
	chmod -R 750 $(INSTALL_SHARE)

	# Create wrapper script
	install -m 755 -o root -g root -d $(INSTALL_BIN)
	echo '#!/bin/bash' > $(INSTALL_BIN)/$(SERVICE_NAME)
	echo 'export PYTHONPATH=$(INSTALL_SHARE):$$PYTHONPATH' >> $(INSTALL_BIN)/$(SERVICE_NAME)
	echo 'exec $(INSTALL_SHARE)/venv/bin/python -m sms_gateway.daemon "$$@"' >> $(INSTALL_BIN)/$(SERVICE_NAME)
	chmod 755 $(INSTALL_BIN)/$(SERVICE_NAME)

	# Install systemd service
	install -m 644 deploy/systemd/sms-gateway.service $(SYSTEMD_DIR)/
	systemctl daemon-reload
	systemctl enable $(SERVICE_NAME).service

	# Set permissions for config directory
	chown -R $(SERVICE_NAME):$(SERVICE_NAME) $(INSTALL_CONF)
	chmod 750 $(INSTALL_CONF)

	@echo "Installation complete."
	@echo "Please:"
	@echo "1. Add your configuration file to $(INSTALL_CONF)/config.json"
	@echo "2. Start the service with: systemctl start $(SERVICE_NAME)"
	@echo "3. Check status with: systemctl status $(SERVICE_NAME)"

uninstall:
	@echo "Uninstalling SMS Gateway..."
	
	# Check for root permissions
	@if [ "$$(id -u)" != "0" ]; then \
		echo "This target must be run as root" >&2; \
		exit 1; \
	fi

	# Stop and disable service
	-systemctl stop $(SERVICE_NAME).service
	-systemctl disable $(SERVICE_NAME).service

	# Remove files and directories
	rm -f $(SYSTEMD_DIR)/$(SERVICE_NAME).service
	rm -f $(INSTALL_BIN)/$(SERVICE_NAME)
	rm -rf $(INSTALL_SHARE)
	rm -rf $(INSTALL_CONF)

	# Remove user and group
	-userdel $(SERVICE_NAME)
	-groupdel $(SERVICE_NAME)

	systemctl daemon-reload
	@echo "Uninstallation complete."