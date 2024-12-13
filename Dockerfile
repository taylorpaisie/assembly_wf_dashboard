# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy application files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Dash will run on
EXPOSE 8050

# Run the Dash app
CMD ["python", "seqera_dashboard.py"]
