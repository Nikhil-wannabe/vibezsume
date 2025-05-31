# Deployment Guide: AI Resume Toolkit (Streamlit App)

This document outlines key considerations for deploying the AI Resume Toolkit Streamlit application.

## 1. Python Environment Management

*   **`requirements.txt`**: This file is crucial and lists all Python dependencies. It should be kept up-to-date.
    ```bash
    pip install -r requirements.txt
    ```
*   **Virtual Environments**: Always use a virtual environment (e.g., `venv` or `conda`) to isolate project dependencies and avoid conflicts with system-wide packages.
    *   **venv:**
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Linux/macOS
        venv\Scripts\activate    # On Windows
        pip install -r requirements.txt
        ```
    *   **conda:**
        ```bash
        conda create -n resume_toolkit_env python=3.10  # Or your preferred Python version
        conda activate resume_toolkit_env
        pip install -r requirements.txt # Can also convert to conda environment.yml if preferred
        ```

## 2. Streamlit App Execution

*   **Basic Command**:
    ```bash
    streamlit run app.py
    ```
*   **Production Command**: For deployment, you'll likely want to specify server options:
    ```bash
    streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
    ```
    *   `--server.port`: Specifies the port (default is 8501).
    *   `--server.address=0.0.0.0`: Makes the app accessible on the network, not just localhost.
    *   `--server.headless=true`: Prevents Streamlit from trying to open a browser window, suitable for servers.
    *   Consider also `--browser.gatherUsageStats=false` for privacy on public deployments.

## 3. Choosing a Hosting Platform

Several options exist, ranging in complexity and control:

*   **Streamlit Community Cloud:**
    *   **Pros:** Easiest for public Streamlit apps, direct deployment from a GitHub repository, handles much of the infrastructure.
    *   **Cons:** Limited resources on the free tier, custom domain configuration might require specific steps or paid features.
    *   **Process:** Connect GitHub repo, select branch and main file (`app.py`). Dependencies from `requirements.txt` are automatically installed.

*   **PaaS (Platform as a Service):** e.g., Heroku, Google App Engine, AWS Elastic Beanstalk.
    *   **Pros:** Manages underlying infrastructure (servers, OS), simplifies deployment scaling.
    *   **Process (General):**
        *   Package the app (often using a `Dockerfile`).
        *   Define a startup command (e.g., in a `Procfile` for Heroku: `web: streamlit run app.py --server.port=$PORT ...`).
        *   Configure platform-specific files (e.g., `app.yaml` for GAE).
        *   Deploy via CLI or Git.

*   **IaaS (Infrastructure as a Service) / VMs:** e.g., AWS EC2, Google Compute Engine, DigitalOcean Droplets.
    *   **Pros:** Full control over the environment.
    *   **Cons:** Requires manual setup of OS, Python, dependencies, web server, security, etc.
    *   **Process:** Provision server, install Python, set up virtual environment, install dependencies, configure a web server (like Nginx) as a reverse proxy, manage security (firewalls, updates).

## 4. Containerization (Docker - Recommended)

Docker provides consistency, portability, and isolation, making it highly recommended for most PaaS/IaaS deployments.

*   **Basic `Dockerfile` Structure:**
    ```dockerfile
    # Use an official Python runtime as a parent image
    FROM python:3.10-slim

    # Set the working directory in the container
    WORKDIR /app

    # Copy the requirements file into the container
    COPY requirements.txt .

    # Install any needed packages specified in requirements.txt
    # Ensure build tools are available if any packages need compilation
    RUN pip install --no-cache-dir -r requirements.txt

    # Download spaCy model (can also be done in app.py on first run if internet is available)
    # RUN python -m spacy download en_core_web_sm
    # Note: If app.py already handles this robustly, this line might be optional here,
    # but including it makes the image more self-contained.

    # Copy the rest of the application code into the container
    COPY . .

    # Make port 8501 available to the world outside this container
    EXPOSE 8501

    # Define environment variables (if any)
    # ENV NAME=value

    # Run app.py when the container launches
    # Use --server.address=0.0.0.0 to ensure it's accessible
    CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
    ```
*   **Build & Run:**
    ```bash
    docker build -t ai-resume-toolkit .
    docker run -p 8501:8501 ai-resume-toolkit
    ```

## 5. Web Server as Reverse Proxy (e.g., Nginx)

For IaaS deployments, using a web server like Nginx as a reverse proxy is standard practice.

*   **Benefits:**
    *   **SSL/TLS Termination:** Handle HTTPS encryption/decryption.
    *   **Custom Domain Mapping:** Easier to point your domain to.
    *   **Load Balancing:** If you scale to multiple instances of your app.
    *   **Serving Static Files:** Though Streamlit handles its own frontend assets, Nginx could serve other static files if needed.
    *   **Security:** Can provide an additional layer of security.
*   **Basic Nginx Configuration Snippet (Conceptual):**
    ```nginx
    server {
        listen 80;
        server_name your_domain.com; # Replace with your domain

        # Redirect HTTP to HTTPS
        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl;
        server_name your_domain.com; # Replace with your domain

        ssl_certificate /etc/letsencrypt/live/your_domain.com/fullchain.pem; # Path to your SSL cert
        ssl_certificate_key /etc/letsencrypt/live/your_domain.com/privkey.pem; # Path to your SSL key

        location / {
            proxy_pass http://localhost:8501; # Assuming Streamlit runs on port 8501
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400; # Adjust as needed
        }
    }
    ```

## 6. Custom Domain Configuration

*   **DNS Settings:** Typically involves adding an `A` record (pointing to your server's IP address) or a `CNAME` record (pointing to the PaaS provider's hostname) in your domain registrar's DNS settings.
*   **Platform-Specific Steps:** Each hosting platform (Streamlit Community Cloud, Heroku, AWS, etc.) will have its own interface and instructions for configuring custom domains.

## 7. SSL/TLS Certificates

*   **Importance:** Essential for HTTPS, ensuring secure communication.
*   **Options:**
    *   **Let's Encrypt:** Provides free SSL certificates. Can be automated with tools like Certbot.
    *   **Platform-Provided:** Many PaaS providers and Streamlit Community Cloud offer automated SSL certificate provisioning and management.
    *   **Commercial Certificates:** Can be purchased from Certificate Authorities.

## 8. Static Assets & Client-Side Libraries

*   **CDN Usage:** This application primarily uses CDNs for GSAP, Three.js, and Lottie animations. This simplifies deployment as these assets are not hosted by our application server directly. Ensure the deployed environment has reliable internet access to these CDNs.
*   **`threejs_scene.html`:** This file is read from the filesystem by `app.py`.
    *   If deploying directly (not in Docker), ensure this file is present in the root directory relative to `app.py`.
    *   If using Docker, the `COPY . .` command in the `Dockerfile` will include it.
*   **Local CSS/JS:** The custom CSS and GSAP JavaScript snippets are embedded directly in `app.py` via `st.markdown`. No separate static file serving is needed for them.

## 9. spaCy Model (`en_core_web_sm`)

*   **Dynamic Download:** The `utils/resume_parser.py` and `utils/job_analyzer.py` files attempt to download the model if it's not found. This requires internet access in the deployment environment during the first run (or first time the model is needed).
*   **Docker Image:** To make the Docker image more self-contained and avoid runtime download issues, you can add this line to your `Dockerfile` after installing requirements:
    ```dockerfile
    RUN python -m spacy download en_core_web_sm
    ```
    This downloads the model during the image build process.
*   **Memory:** Be mindful that spaCy models consume memory. `en_core_web_sm` is small, but if larger models were used, ensure your deployment environment has sufficient RAM.

## 10. Data Persistence (`data/` directory)

*   The application uses `data/predefined_options.json`. This file must be included in the deployment package (e.g., copied into the Docker image).
*   The `data/` directory is also used to temporarily store uploaded resume files during parsing in `app.py`.
    *   On platforms like Heroku or some serverless environments, the local filesystem might be ephemeral. This is generally fine for temporary storage as the file is deleted after processing.
    *   If persistent storage of user data were required (it's not for this app), a database or external storage solution (like AWS S3) would be necessary.

This guide provides a starting point. Specific deployment steps will vary based on the chosen platform and infrastructure.
