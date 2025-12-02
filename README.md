# Kubeflow Ground Project

This project is a visual builder for Kubeflow Pipelines, consisting of a Vue.js frontend and a FastAPI backend.

## Project Structure

- **frontend/**: A Vue 3 + Vite application providing the drag-and-drop interface.
- **backend/**: A Python FastAPI service that handles component management and pipeline compilation.

## Prerequisites

- **Node.js**: v16 or higher
- **Python**: v3.8 or higher
- **Kubeflow Pipelines**: Access to a KFP cluster (optional for UI development, required for running pipelines).

## Getting Started

### 1. Backend Setup

The backend runs on port `8000`.

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  (Optional) Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Start the server:
    ```bash
    python -m uvicorn main:app --reload --port 8000
    ```

    The API documentation will be available at http://localhost:8000/docs.

### 2. Frontend Setup

The frontend runs on port `5173` (default Vite port).

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Start the development server:
    ```bash
    npm run dev
    ```

### 3. Usage

1.  Ensure both backend and frontend servers are running.
2.  Open your browser and visit: http://localhost:5173
3.  Navigate to the **Pipeline Builder** page (usually via the sidebar or direct link `/pipelines`).
4.  **Drag and Drop** components from the left sidebar to the canvas.
5.  **Connect** nodes to define the workflow.
6.  **Click** on a node to configure its arguments and resource limits in the right-side property panel.
7.  Click **Run Pipeline** to compile and submit the pipeline to Kubeflow.
