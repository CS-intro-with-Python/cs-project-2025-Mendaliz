# CookBook

## Description

A simple recipe storage application with a tagging system and shopping list functionality.

### Main Scenario:
1. Save a recipe (can include a link to the source)
2. Edit the recipe if necessary
3. Filter by tags for quick search
4. Select recipes you plan to cook
5. Check if you have enough ingredients

## Interface

### Main Page (`/`)
- Tag filter panel
- Form for adding new recipes
- List of all recipes with pagination
- For each recipe:
  - "View" button to view details
  - Checkbox to add to shopping list
  - Clickable tags
- Button to create shopping list
- Button to update recipes

### Recipe Page (`/recipe/{id}`)
- Complete recipe information
- Link to source (if available)
- List of tags (clickable)
- Edit and delete buttons

### Edit Page (`/recipe/{id}/edit`)
- Form to edit all recipe fields
- Save changes button
- Cancel button

### Shopping List Page (`/recipe/checklist`)
- Information about ingredients needed for selected recipes

## Web Pages

| Path | Description | Requires Authentication |
|------|-------------|-------------------------|
| `/` | Main page with recipe list | yes |
| `/auth` | Login/registration page | no |
| `/logout` | Logout | yes |
| `/recipe/{id}` | View specific recipe | yes |
| `/recipe/{id}/edit` | Edit recipe | yes |
| `/recipe/checklist` | View shopping list | yes |

## API Summary

| Method | Path | Description | Requires Authentication |
|--------|------|-------------|-------------------------|
| POST | `/api/register` | User registration | no |
| POST | `/api/login` | User login | no |
| GET | `/api/check-auth` | Check authentication status | no |
| GET | `/api/recipes` | Get recipe list | yes |
| POST | `/api/recipes` | Create recipe | yes |
| GET | `/api/recipes/{id}` | Get specific recipe | yes |
| PUT | `/api/recipes/{id}` | Update recipe | yes |
| DELETE | `/api/recipes/{id}` | Delete recipe | yes |
| GET | `/api/tags` | Get all tags | yes |
| GET | `/api/meals` | Get all ingredients for selected recipes | yes |

## Setup

```
# Build the Docker image
docker build -t flask-app .

# Run the container
docker run -d -p 8080:5000 --name flask-container flask-app

# Test the application
curl http://localhost:8080/
```

## Requirements

Backend Framework: Flask 2.3.3

Programming Language: Python 3.9+

Containerization: Docker

Dependencies: See requirements.txt

## Git

Latest stable version branch: main