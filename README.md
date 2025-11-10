# SmartTransit Project: Running the Application

This guide explains how to set up and run the SmartTransit backend (Dockerized) and frontend (React Native with Expo Go) on your local development machine.

## Prerequisites

Before you begin, ensure you have the following installed and configured:

1.  **Git:** For cloning the repository.
2.  **Docker & Docker Compose:** Required to run the containerized backend and Stripe CLI. [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Windows/Mac) includes both. Ensure Docker is running.
3.  **Node.js & npm:** Required for the React Native frontend. [Download Node.js](https://nodejs.org/). npm is included.
4.  **Android Studio:** Required for running the Android Emulator. [Download Android Studio](https://developer.android.com/studio).

## Environment Setup

Sensitive configuration details like API keys and database credentials are managed using environment files. **You will need to ask a team member for the actual values to populate these files.**

### 1. Backend (`Backend/.env`)

*   Navigate to the `Backend/` directory in the project.
*   Create a file named `.env`.
*   Copy the following structure into the file and ask a team member for the values:

## Running the Backend (Docker)

The backend runs inside Docker containers managed by Docker Compose. This includes the Flask application and the Stripe CLI for local webhook forwarding.

1.  **Navigate to Backend Directory:**
    ```bash
    cd path/to/your/SmartTransit/Backend
    ```
    *(Use WSL terminal if running Docker via WSL2 backend, otherwise use standard terminal)*

2.  **Ensure `Backend/.env` is created and populated**.

3.  **Build and Start Containers:**
    ```bash
    docker-compose up --build
    ```
    *   `--build`: Required the first time or if you change `Dockerfile` or `requirements.txt`. For subsequent runs, `docker-compose up` is often sufficient.
    *   This command will build the Flask backend image, download the Stripe CLI image, and start both containers.
    *   You should see output from both `flask_backend_service` and `stripe_cli_service`. The Stripe CLI will log that it's ready and forwarding webhooks.

4.  **Backend Access:** The backend API will be accessible on port 8000 of your host machine (e.g., `http://localhost:8000` from your host browser, or the specific IPs needed by emulators/devices).

5.  **Stopping the Backend:** Press `Ctrl+C` in the terminal where `docker-compose up` is running. To remove the containers afterwards, run `docker-compose down`.

## Running the Frontend (Expo Go)

The frontend is a React Native application managed using Expo.

1.  **Navigate to Frontend Directory:**
    ```bash
    cd path/to/your/SmartTransit/Frontend
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Prepare Android Emulator (via Android Studio):**
    *   Open Android Studio.
    *   Click **More Actions** > **Virtual Device Manager**.
    *   If you don't have a suitable virtual device, click **Create device** and follow the prompts to set one up (choose a phone model and system image).
    *   Select the virtual device you want to use and click the **Launch** button (looks like a green play triangle). Wait for the emulator to fully boot up.

4.  **Start Metro Bundler:**
    ```bash
    npm start
    ```
    *   This command starts the Metro development server, which bundles your JavaScript code. It will display a QR code in the terminal.

5.  **Connect Expo Go App:**
    *   Ensure the Android Emulator you launched is running.
    *   Open the **Expo Go** app on the emulator/device (you will need to install it from the Play Store)
    *   Copy the url given by `Metro waiting on <url>` and paste into Expo Go under `Enter URL manually`.
    *   The app will download the JavaScript bundle from Metro and launch.

## Backend Testing

Unit and integration tests for the backend are run using `pytest`.

1.  Navigate to the `Backend/` directory in your terminal.
2.  Ensure necessary test dependencies are installed (they should be included in `requirements.txt`).
3.  Run tests:

    *   **Run all tests:**
        ```bash
        pytest
        ```
    *   **Run tests with coverage report (HTML):**
        ```bash
        pytest --cov=backend --cov-report=html
        ```
    *   **Run specific tests by name matching:**
        ```bash
        pytest -k <test_name_substring>
        ```