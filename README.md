# Feature Roadmap Tool

This is a Streamlit application for visualizing feature roadmaps and team load.

## Setup

To run this application, you need to set up the environment correctly. The application requires a non-snap version of Chromium for the image export feature to work.

1.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install system dependencies:**
    Run the `setup.sh` script to install the correct version of Chromium.
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

## Running the application

Once the setup is complete, you can run the Streamlit application with:
```bash
streamlit run app.py
```
