# Base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt ./

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]