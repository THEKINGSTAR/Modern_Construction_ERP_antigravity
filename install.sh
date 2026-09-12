#!/bin/bash
# install.sh - Installs requirements for Modern Construction ERP on Linux

set -e

echo "Starting installation for Modern Construction ERP (Production)..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Update package list (Debian/Ubuntu or RHEL/CentOS)
echo "Updating package list..."
if command_exists apt-get; then
    apt-get update -y
elif command_exists yum; then
    yum check-update -y || true
else
    echo "Warning: Unsupported package manager. Skipping system update."
fi

# Install Docker if not installed
if command_exists docker; then
    echo "Docker is already installed."
else
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    if command_exists systemctl; then
        systemctl enable docker
        systemctl start docker
    fi
fi

# Install Docker Compose if not installed
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    echo "Docker Compose is already installed."
else
    echo "Installing Docker Compose..."
    if command_exists apt-get; then
        apt-get install -y docker-compose-plugin
    elif command_exists yum; then
        yum install -y docker-compose-plugin
    else
        echo "Installing docker-compose manually..."
        curl -SL "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
fi

# Setup .env file
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo ".env created. PLEASE EDIT .env WITH YOUR PRODUCTION SECRETS!"
    else
        echo "Warning: .env.example not found. Please create .env manually."
    fi
else
    echo ".env file already exists."
fi

echo "Installation complete!"
echo "Please edit the .env file with your specific configuration."
echo "Then, use './run.sh' to start the project."
