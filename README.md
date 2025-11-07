[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DESIFpxz)
# CS_2024_project - Flask Docker Application

## Description

This is a client-server Flask application containerized with Docker. The project demonstrates modern development practices including REST API implementation, containerization, CI/CD pipelines, and automated testing. The application features a Flask server with multiple endpoints and a client for testing API responses.

## Setup

### Using Docker (Recommended)
```bash
# Build the Docker image
docker build -t flask-app .

# Run the container
docker run -d -p 5000:5000 --name flask-container flask-app

# Test the application
curl http://localhost:8080/hello
Using Docker Compose
bash
# Start the application with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f
Local Development
bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py

# In another terminal, test with client
python client.py
Requirements
Backend Framework: Flask 2.3.3

Programming Language: Python 3.9+

Containerization: Docker + Docker Compose

CI/CD: GitHub Actions

Deployment: Railway.app

Testing: Custom client with HTTP requests

Dependencies: See requirements.txt

Features
RESTful API with multiple endpoints (/hello, /user/<name>, /search)

Docker containerization for easy deployment

Continuous Integration with GitHub Actions

Continuous Deployment to Railway.app

Automated health checks and testing

Environment variable configuration

Colored output and GitHub Actions annotations

Live deployment at: https://your-app-name.railway.app

Git
Stable Branch: main
The main branch always contains the latest stable version of the application. Feature development happens in separate branches and is merged via pull requests after passing all tests.

Success Criteria
✅ Application successfully builds and runs in Docker container

✅ All API endpoints return correct HTTP status codes and responses

✅ CI/CD pipeline passes all automated tests on each commit

✅ Application is automatically deployed to Railway.app

✅ Client can successfully communicate with the server

✅ Code follows best practices and includes proper documentation

✅ Health checks confirm application is running correctly

API Endpoints
GET /hello - Returns greeting message

GET /user/<username> - Returns personalized greeting

GET /search?q=<query> - Returns search query information

Deployment
The application is automatically deployed to Railway when changes are pushed to the main branch. The live version is available at the provided Railway URL.

Testing
Run the test client to verify all endpoints:

bash
python client.py
For colored output and GitHub Actions annotations:

bash
python client_colored.py