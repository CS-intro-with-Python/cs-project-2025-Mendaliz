# CS_2024_project

## Description

This is a client-server Flask application containerized with Docker. The project demonstrates modern development practices including REST API implementation, containerization, CI/CD pipelines, and automated testing. The application features a Flask server with one endpoint and a client for testing API responses.

url: http://cs-project-2025-mendaliz-production.up.railway.app

## Setup

``` bash
# Build the Docker image
docker build -t flask-app .

# Run the container
docker run -d -p 8080:8080 --name flask-container flask-app

# Test the application
curl http://localhost:8080/
```

## Requirements

Backend Framework: Flask 2.3.3

Programming Language: Python 3.9+

Containerization: Docker

CI/CD: GitHub Actions

Deployment: Railway.app

Testing: Custom client with HTTP requests

Dependencies: See requirements.txt

## Features

RESTful API with one endpoint( / )

Docker containerization for easy deployment

Continuous Integration with GitHub Actions

Continuous Deployment to Railway.app

Automated health checks and testing

Environment variable configuration inside container

Colored output and GitHub Actions annotations

Live deployment at: http://cs-project-2025-mendaliz-production.up.railway.app

## Git

Stable Branch: main
The main branch always contains the latest stable version of the application. Feature development happens in separate branches and is merged via pull requests after passing all tests.

## Success Criteria

✅ Application successfully builds and runs in Docker container

✅ All API endpoints return correct HTTP status codes and responses

✅ CI/CD pipeline passes all automated tests on each commit

✅ Application is automatically deployed to Railway.app

✅ Client can successfully communicate with the server

## API Endpoints

GET / - Returns greeting message

## Deployment

The application is automatically deployed to Railway when changes are pushed to the main branch. The live version is available at the provided Railway URL.