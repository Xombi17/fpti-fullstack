# FPTI Application Development Roadmap

This file outlines the tasks needed to enhance the Financial Portfolio Tracking Interface. The tasks are organized into phases, starting with foundational improvements and moving to more advanced features.

---

## Phase 1: Core Functionality & Frontend Integration

**Goal:** Replace all mock data in the frontend with live data from the backend API.

-   [ ] **Dashboard Tab:**
    -   [ ] Connect the "Total Portfolio Value" card to the `/api/v1/portfolios/{portfolio_id}/value` endpoint.
    -   [ ] Implement logic to calculate and display "Today's Change" and "Best Performer".
    -   [ ] Populate the "Portfolio Value Over Time" chart using historical data from the backend.
    -   [ ] Connect the "Asset Allocation" pie chart to the `/api/v1/portfolios/{portfolio_id}/allocation` endpoint.
    -   [ ] Populate the "Current Holdings" table with real data.

-   [ ] **Transactions Tab:**
    -   [ ] Create a new layout in `frontend/app.py` for the "Transactions" tab.
    -   [ ] Add a `dash_table.DataTable` to display a list of all transactions.
    -   [ ] Fetch data from the `/api/v1/transactions/` endpoint.
    -   [ ] Add a form to allow users to manually add new transactions (POST to `/api/v1/transactions/`).

-   [ ] **Analysis Tab:**
    -   [ ] Connect the "Performance Metrics" section to the `/api/v1/analytics/portfolio/{portfolio_id}/performance` endpoint.
    -   [ ] Connect the "Risk Analysis" section to the `/api/v1/analytics/portfolio/{portfolio_id}/risk-metrics` endpoint.

---

## Phase 2: User Authentication

**Goal:** Implement a secure user login and registration system.

-   [ ] **Backend:**
    -   [ ] Create a new router file `backend/app/routers/auth.py`.
    -   [ ] Implement password hashing using `passlib`.
    -   [ ] Create a `/token` endpoint for users to log in and receive a JWT token.
    -   [ ] Create a `/register` endpoint for new users to create an account.
    -   [ ] Implement dependency injection to protect routes and ensure only authenticated users can access their own data.

-   [ ] **Frontend:**
    -   [ ] Create a login page.
    -   [ ] Implement logic to store the JWT token in the user's browser (e.g., in `dcc.Store`).
    -   [ ] Send the JWT token in the `Authorization` header for all API requests.
    -   [ ] Add a "Logout" button to clear the token.

---

## Phase 3: Net Worth and Budgeting Features

**Goal:** Add modules for tracking net worth and managing budgets.

-   [ ] **Net Worth Module (Backend):**
    -   [ ] Create a new router file `backend/app/routers/net_worth.py`.
    -   [ ] Create endpoints to add/update/delete assets (e.g., real estate, vehicles) and liabilities (e.g., mortgages, loans).
    -   [ ] Create an endpoint to calculate and retrieve the user's current net worth.
    -   [ ] Implement a background task to take a daily `NetWorthSnapshot`.

-   [ ] **Net Worth Module (Frontend):**
    -   [ ] Add a new "Net Worth" tab to the main navigation.
    -   [ ] Create a layout with cards for "Total Assets," "Total Liabilities," and "Net Worth."
    -   [ ] Add a line chart to visualize the net worth trend over time using the snapshot data.
    -   [ ] Add tables to display the breakdown of assets and liabilities.

-   [ ] **Budgeting Module (Backend):**
    -   [ ] Create a new router file `backend/app/routers/budgets.py`.
    -   [ ] Create CRUD endpoints for managing budgets (`Budget` model).
    -   [ ] Create an endpoint to link transactions to budget categories and update the `current_spent` amount.

-   [ ] **Budgeting Module (Frontend):**
    -   [ ] Add a new "Budgeting" tab.
    -   [ ] Create a layout to display a user's budgets with progress bars showing spending against limits.
    -   [ ] Add a form to create and edit budgets.

---

## Phase 4: Advanced Analytics & Reporting

**Goal:** Enhance the analytics capabilities and add reporting features.

-   [ ] **Backend:**
    -   [ ] In `backend/app/routers/analytics.py`, replace placeholder values with real calculations using the `DataAnalyzer` utility.
    -   [ ] Implement the calculation for Sharpe ratio, volatility, and max drawdown using historical price data.
    -   [ ] Create an endpoint to generate a PDF summary of a portfolio's performance.

-   [ ] **Frontend:**
    -   [ ] In the "Analysis" tab, add more advanced charts, such as a rolling volatility chart.
    -   [ ] Add a "Download Report" button that calls the PDF generation endpoint.