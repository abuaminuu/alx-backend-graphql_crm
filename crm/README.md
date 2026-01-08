# CRM Celery Task Setup Guide

This document explains how to set up and run Celery tasks for the CRM application.

## Prerequisites

### 1. Install Redis
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
sudo systemctl start redis  # Ubuntu
# or
brew services start redis   # macOS

# Verify Redis is running
redis-cli ping
# Should return: PONG