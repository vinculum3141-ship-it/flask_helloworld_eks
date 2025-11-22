# This Dockerfile creates a minimal Docker image for running a Flask application.
# It uses the lightweight Python 3.11-slim base image, sets the working directory to /app,
# copies the requirements and app files, installs dependencies, exposes port 5000,
# and sets the default command to run the Flask app with 'python app.py'.
# This setup is commonly used to containerize and deploy Python web applications.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
# Ensure pip is up-to-date, then install pinned dependencies from requirements.txt
RUN python -m pip install --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

# Keep Python output unbuffered (helpful for logging in containers)
ENV PYTHONUNBUFFERED=1
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
