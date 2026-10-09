# ACEest Fitness & Gym — DevOps Assignment 1

**Student:** Himanshu  
**Student ID:** 2025tm93219  
**Course:** Introduction to DevOps (CSIZG514/SEZG514)

## Overview

ACEest is a small Flask service for fitness client records and weekly adherence tracking. This repository demonstrates the development-to-build workflow requested in the assignment: version control, automated tests, Docker packaging, a GitHub Actions workflow, and a Jenkins build pipeline.

The original supplied examples included desktop Tkinter screens. For this assignment, the core fitness-management functionality is exposed through a Flask web application and JSON endpoints, as required by the assignment brief.

## Features

- Create, list, retrieve, update, and delete client records.
- Choose a Fat Loss, Muscle Gain, or Beginner program.
- Estimate calories using the selected program's configured factor.
- Record and retrieve weekly adherence percentages.
- Validate inputs and return useful HTTP status codes.
- Store data in SQLite.
- Check service health at `/health`.

## Local setup

Python 3.12 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment:

- macOS/Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`

Install dependencies and start the service:

```bash
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000/` in a browser. The SQLite database is created automatically. By default it is `aceest_fitness.db`; set `ACEEST_DB_PATH` to change its location.

## API quick reference

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/clients` | List clients |
| POST | `/api/clients` | Create a client |
| GET | `/api/clients/<id>` | Retrieve one client |
| PUT | `/api/clients/<id>` | Update a client |
| DELETE | `/api/clients/<id>` | Delete a client |
| GET | `/api/clients/<id>/progress` | List weekly progress |
| POST | `/api/clients/<id>/progress` | Add weekly adherence |

Example client request:

```bash
curl -X POST http://127.0.0.1:5000/api/clients \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Himanshu","age":24,"weight":75,"program":"Muscle Gain"}'
```

A successful creation returns HTTP `201`. Duplicate names return `409`; invalid input returns `400`; missing client records return `404`.

## Run tests manually

```bash
python -m pip install -r requirements.txt
pytest -q
```

The tests use a temporary SQLite database, so they do not change the normal local database.

## Docker

Build and run the container:

```bash
docker build -t aceest-fitness:local .
docker run --rm -p 5000:5000 -v aceest-data:/app/data aceest-fitness:local
```

Then visit `http://127.0.0.1:5000/`. The image uses a slim Python base image, runs as a non-root user, and defines a health check.

Run the test suite inside the built image:

```bash
docker run --rm --entrypoint pytest aceest-fitness:local -q
```

## GitHub Actions workflow

The workflow is stored at `.github/workflows/main.yml` and runs for every push and pull request. It checks out the repository, installs Python dependencies, checks Python syntax, runs the tests, builds the Docker image, and runs the tests inside that image. The workflow needs no repository secrets because it does not publish an image.

## Jenkins build

The root `Jenkinsfile` defines checkout, syntax/build, and containerized-test stages. To use it:

1. Run Jenkins on a machine or agent with Git, Python 3, and Docker installed and available to the Jenkins user.
2. Create a Pipeline job and connect it to this GitHub repository.
3. Select **Pipeline script from SCM**, choose Git, and point to the repository's branch.
4. Configure a GitHub webhook to the Jenkins endpoint and enable the GitHub hook trigger, or use a configured polling strategy.
5. Run the job and review the stage logs.

Jenkins is a second build gate; GitHub Actions provides the per-push and pull-request checks. The Jenkins pipeline builds a uniquely tagged image, tests it, and removes the temporary image afterward.

## Suggested Git workflow

Use a feature branch for each change and descriptive commits, for example:

```bash
git init
git add .
git commit -m "feat: add Flask fitness client API"
git switch -c feature/ci-pipeline
git add .github/workflows/main.yml Dockerfile Jenkinsfile
git commit -m "ci: add Docker and automated build checks"
```

Create a **public** repository on GitHub, then connect and push your local repository:

```bash
git branch -M main
git remote add origin https://github.com/<your-username>/aceest-fitness-devops.git
git push -u origin main
git push -u origin feature/ci-pipeline
```

Replace `<your-username>` with your GitHub username. After pushing, check the **Actions** tab and confirm the workflow passes. The public GitHub URL is the final link to submit.

## Scope and assumptions

- Calorie values are simple estimates based on body weight multiplied by a program factor; they are not medical or dietetic advice.
- Authentication and production deployment are outside the scope stated in the assignment brief.
- SQLite is suitable for this assignment-sized demonstration. A production deployment would need further security, configuration, monitoring, and data-management work.
