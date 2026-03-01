#!/bin/bash

set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# Update and upgrade apt settings and apps
apt update && apt upgrade -y

if [ -f /app/requirements_apt.txt ]; then
  xargs apt install -y < /app/requirements_apt.txt
else
  echo "Skipping root apt requirements: /app/requirements_apt.txt not found"
fi

# Run the project's main requirements.txt
if [ -f /app/requirements.txt ]; then
  pip install -r /app/requirements.txt
else
  echo "Skipping root pip requirements: /app/requirements.txt not found"
fi

for tool in /app/superagi/tools/* /app/superagi/tools/external_tools/* /app/superagi/tools/marketplace_tools/* ; do
# Loop through the tools directories and install their apt_requirements.txt if they exist
  if [ -d "$tool" ] && [ -f "$tool/requirements_apt.txt" ]; then
    echo "Installing apt requirements for tool: $(basename "$tool")"
    xargs apt install -y < "$tool/requirements_apt.txt"
  fi
# Loop through the tools directories and install their requirements.txt if they exist
  if [ -d "$tool" ] && [ -f "$tool/requirements.txt" ]; then
    echo "Installing requirements for tool: $(basename "$tool")"
    pip install -r "$tool/requirements.txt"
  fi
done
