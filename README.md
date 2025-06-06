# Caspinex E-commerce Platform

Caspinex is an e-commerce platform built with Django (backend) and React (frontend).

## Project Structure

-   `caspinex/`: Contains the Django backend project.
    -   `shop/`: The main Django app for e-commerce logic (users, products, orders, API).
    -   `templates/`: Contains custom Django admin templates (e.g., for order revenue display).
    -   `manage.py`: Django's command-line utility.
    -   `.env.sample`: Sample environment file for Django backend.
-   `frontend/`: Contains the React frontend project.
    -   `caspinex-client/`: The React application.
-   `requirements.txt`: Python dependencies for the backend (located in the project root).
-   `.gitignore`: Specifies intentionally untracked files that Git should ignore (in project root).
-   `README.md`: This file.

## Technology Stack

-   **Backend**: Django, Django Rest Framework, Python
-   **Frontend**: React (with TypeScript), Bootstrap, Axios, React Router
-   **Database**: Configurable (e.g., MySQL, PostgreSQL). Uses SQLite by default for easy setup.
-   **Authentication**: JWT (JSON Web Tokens) via djangorestframework-simplejwt

## Backend Setup (Django)

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Create and activate a Python virtual environment:**
    (It's recommended to do this in the project root directory `<repository-name>`)
    ```bash
    python3 -m venv venv
    # On Windows: venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    (From the project root directory where `requirements.txt` is located)
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables for the backend:**
    -   Navigate to the Django project directory: `cd caspinex`
    -   Copy the sample environment file:
        ```bash
        cp .env.sample .env
        ```
    -   Edit the `caspinex/.env` file with your actual settings (database credentials, `SECRET_KEY`, etc.).
        **Important:** Generate a new, strong `SECRET_KEY`. For development, the default SQLite database (`db.sqlite3`) will be created in the `caspinex/` directory.

5.  **Apply database migrations:**
    (From the `caspinex/` directory where `manage.py` is)
    ```bash
    python3 manage.py migrate
    ```

6.  **Create a superuser (admin user):**
    (From the `caspinex/` directory)
    ```bash
    python3 manage.py createsuperuser
    ```
    Follow the prompts to set email, password, etc.

7.  **Run the Django development server:**
    (From the `caspinex/` directory, e.g., by running 'python3 manage.py runserver')
    The backend API will typically be available at `http://127.0.0.1:8000/api/v1/shop/`.
    The admin panel will be at `http://127.0.0.1:8000/admin/`.

## Frontend Setup (React)

1.  **Navigate to the React client directory:**
    ```bash
    cd frontend/caspinex-client
    ```

2.  **Install Node.js dependencies:**
    (Ensure you have Node.js and npm installed. A version compatible with `react-router-dom@^7.6.2` e.g., >=20.0.0 might be needed for full feature compatibility.)
    ```bash
    npm install
    ```

3.  **Run the React development server:**
    (From the `frontend/caspinex-client/` directory, e.g., by running 'npm start')
    The frontend application will typically be available at `http://localhost:3000`.

## Running Tests (Placeholder)

-   **Backend**: `python3 manage.py test shop` (from `caspinex/` directory)
-   **Frontend**: `npm test` (from `frontend/caspinex-client/` directory)

## Linting (Placeholder)

-   Consider using tools like Flake8 for Python and ESLint/Prettier for React/TypeScript.

## Contributing

Please follow standard Git workflow (fork, branch, commit, pull request).

---
This README provides basic setup instructions. Further details on API endpoints, data models, and contribution guidelines will be added as the project evolves.

## Further Details on API Endpoints


### Product Listing Endpoint (`/api/v1/shop/products/`)

This endpoint lists available products and supports pagination, filtering, and ordering.

**Supported Query Parameters (as defined in `ProductFilter`):**

*   **Filtering:**
    *   `name`: Search for products by name (case-insensitive, partial match, using `icontains`).
        *   Example: `/api/v1/shop/products/?name=لپتاپ` (searches for names containing 'لپتاپ')
    *   `category_slug`: Filter products by the exact slug of their category (case-insensitive, using `iexact`).
        *   Example: `/api/v1/shop/products/?category_slug=لپ-تاپ`
    *   `category_name`: Search for products by their category name (case-insensitive, partial match, using `icontains`).
        *   Example: `/api/v1/shop/products/?category_name=کتاب`
    *   `min_price`: Filter products with a price greater than or equal to the given value.
        *   Example: `/api/v1/shop/products/?min_price=1000000`
    *   `max_price`: Filter products with a price less than or equal to the given value.
        *   Example: `/api/v1/shop/products/?max_price=50000000`
    *   `available`: Filter products by their availability status (`true` or `false`).
        *   Example: `/api/v1/shop/products/?available=true`

*   **Ordering:**
    *   `ordering`: Sort products. Prepend a hyphen (`-`) for descending order.
        *   Available fields for ordering (as defined in `ProductFilter`): `price`, `name`, `created_at`, `updated_at`.
        *   Example (ascending by price): `/api/v1/shop/products/?ordering=price`
        *   Example (descending by price): `/api/v1/shop/products/?ordering=-price`
        *   Example (newest first by creation date): `/api/v1/shop/products/?ordering=-created_at`

*   **Combining Filters:**
    *   You can combine multiple filter parameters.
        *   Example: `/api/v1/shop/products/?category_slug=لپ-تاپ&available=true&min_price=30000000&ordering=name`

**Note on Persian Characters in URLs:** When using Persian characters in URL query parameters, ensure they are properly URL-encoded (e.g., `لپ-تاپ` becomes `%D9%84%D9%BE-%D8%AA%D8%A7%D9%BE`). Most HTTP clients and browsers handle this automatically.
