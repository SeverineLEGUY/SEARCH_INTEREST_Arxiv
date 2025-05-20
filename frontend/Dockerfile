FROM python:3.12-slim

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Try and run pip command after setting the user with `USER user` to avoid permission issues with Python
RUN pip install --no-cache-dir --upgrade pip

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user *.py $HOME/app
COPY --chown=user requirements.txt $HOME/app

# Install any other Python dependencies (e.g., from requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port we run on (8501)
EXPOSE 8501

# Command to run Streamlit app when the container starts
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]

