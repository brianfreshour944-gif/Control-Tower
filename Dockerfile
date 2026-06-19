FROM python:3.11-slim

WORKDIR /app

# Copy the requirements file first for better caching
COPY requirements.txt .

# Install dependencies using the file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
