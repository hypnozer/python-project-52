# Task Manager

[![Actions Status](https://github.com/hypnozer/python-project-52/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/hypnozer/python-project-52/actions)
[![Python CI](https://github.com/hypnozer/python-project-52/actions/workflows/pyci.yml/badge.svg)](https://github.com/hypnozer/python-project-52/actions/workflows/pyci.yml)

Task management web application built with Python and Django.

## Development

Create a local environment file and install the project dependencies:

```bash
cp .env.example .env
make install
```

Apply migrations and start the development server:

```bash
make migrate
make dev
```

The application will be available at http://127.0.0.1:8000/.

Run tests and the linter:

```bash
make check
```

Run tests with coverage:

```bash
make test-coverage
```

## Deployment

The application is prepared for deployment on Render with PostgreSQL.

- Build command: `make build`
- Start command: `make render-start`
- Required environment variables: `DATABASE_URL`, `SECRET_KEY`

The public application URL will be added after the Render service is created.
