# Setup environment
FROM python:3.9-bullseye

# Install requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Copy files
COPY src/* src/

# Set /src as working directory
WORKDIR /src

# Run the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
