# AgentScope Workstation User Guide

## Introduction

AgentScope Workstation is a powerful workflow platform that supports knowledge base functionality. This document will guide you through the environment setup and system startup process.

## System Requirements

- **Docker & Docker Compose**: It is recommended to run this application in a Docker environment.
- **DashScope API Key**: A valid DashScope API Key is required to use the knowledge base functionality.

## Quick Start

### 1. Environment Configuration

First, create the configuration file:

```
cp .env.example .env
```

Open the `.env`  file for editing:

- Mandatory: Fill in the DASHSCOPE_API_KEY to enable knowledge base functionality.
- Optional: Modify Redis and MySQL connection parameters as needed.

### 2. Generate RSA key paris

Run the following codes to generate RSA keys

``````
bash generate_rsa_keys.sh
``````

### 3. Start Services

```
# Enter the docker directory
cd docker

# Start all services
docker-compose up
```

This will start the following services:

- Weaviate (vector database for the knowledge base)
- Redis (default password: redis_password)
- MySQL (user: agentscope, password: Agentscope123)
- Celery (background task processing)
- API (backend service)

### 4. Initialize Database

The MySQL database needs to be initialized for first-time use:

```
# Ensure you are in the docker directory
bash mysql-init/insert_data.sh
```

This script will create:

- User accounts:
  - Username: agentscope, Password: 123456
  - Username: admin, Password: 123456
- Model configurations
- API key settings

### 5. Access the System

After initialization, open your browser and visit:

```
workstation.agentscope.io
```

Log in to the system using the above account information.

## Configuration Details

### Environment Variables

All system configurations can be adjusted in the .env file, mainly including:

- Database connection information
- API keys
- Service ports

## Notes

1. Knowledge Base Dependencies
   - A valid DashScope API Key is required.
   - The knowledge base functionality relies on the Weaviate vector database.
   - The current version does not support online registration of embedding models; the next version will support it.
2. Using Without Docker
   - If not using the knowledge base functionality, Docker is optional.
   - However, you will need to configure and start MySQL and Redis services manually.
3. Data Persistence
   - By default, data will be stored in Docker volumes.
   - Recreating containers will not result in data loss.

## Troubleshooting

1. Database Connection Issues
   1. Check if the configuration in .env is correct.
   2. Ensure the MySQL container is running: docker ps | grep mysql
2. **Table Not Found Error**: Re-run the initialization script: bash mysql-init/insert_data.sh

------

If you have any questions or need technical support, please refer to the project documentation or submit an issue.

Enjoy using AgentScope Workstation!