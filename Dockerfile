FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install dependencies
# We don't have a requirements.txt, so we install them directly
RUN pip install streamlit ccxt pandas numpy sqlalchemy psycopg2-binary alpaca-py plotly

# Copy your files into the container
COPY . .

# Expose the port
EXPOSE 8501

# Start the application
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
