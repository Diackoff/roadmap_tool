#!/bin/bash
# This script sets up the environment for the Feature Roadmap Tool.
# It removes the default snap-based chromium and installs a non-snap version from a PPA.

# Remove the old, snap-based chromium packages
sudo apt-get remove -y chromium-browser chromium-chromedriver

# Add the xtradeb/apps PPA
sudo add-apt-repository -y ppa:xtradeb/apps

# Update package lists
sudo apt-get update

# Install the non-snap version of chromium
sudo apt-get install -y chromium
