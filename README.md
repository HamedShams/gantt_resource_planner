# resource_allocator

A FastAPI-based resource allocation web app with XML config persistence.

## Features
- FastAPI backend with Jinja2 templating
- Reads/writes resource_config.xml for persistent config
- All static/templates included
- Dockerized for production deployment

## Project Structure
```
resource_allocator/
├── main.py
├── requirements.txt
├── resource_config.xml
├── templates/
│   ├── index.html
│   ├── gantt.html
│   └── edit.html
├── Dockerfile
├── .dockerignore
└── README.md
```

## Running Locally
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Docker Usage
Build and run the container:
```bash
docker build -t resource_allocator .
docker run -p 8000:8000 -v $(pwd)/resource_config.xml:/app/resource_config.xml resource_allocator
```

- The XML config is persisted as a file. To avoid data loss, mount it as a Docker volume as above.

## Deploying to Railway
1. Push all files to your GitHub repo.
2. Connect the repo to Railway.com.
3. Railway will auto-detect the Dockerfile and build your app.
4. (Optional) Mount persistent storage for `resource_config.xml` via Railway's volumes feature to ensure config changes persist across deploys.

---
For questions, contact HamedShams.
