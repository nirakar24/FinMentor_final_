# SetuDemo - Account Aggregator Integration

This project demonstrates an integration with the Setu Account Aggregator ecosystem using .NET Core. It supports storing data in either **MongoDB** or **MySQL**.

## 🚀 Getting Started

### Prerequisites
- .NET 8.0 SDK
- MongoDB Server (local or remote)
- MySQL Server (local or remote)

### Configuration

The application uses `appsettings.json` to configure the database provider.

#### 1. Using MongoDB
To use MongoDB, set `"UseSql": false` in `appsettings.json`.

```json
{
  "UseSql": false,
  "Mongo": {
    "ConnectionString": "mongodb://localhost:27017",
    "Database": "finmentor",
    "TransactionsCollection": "transactions",
    "ConsentsCollection": "consents"
  }
}
```

#### 2. Using MySQL
To use MySQL, set `"UseSql": true` in `appsettings.json` and provide the connection string.

```json
{
  "UseSql": true,
  "ConnectionStrings": {
    "DefaultConnection": "server=localhost;user=root;password=password;database=finmentor"
  }
}
```

**First-time Setup for MySQL:**
You need to apply migrations to create the database schema.
```bash
dotnet ef database update
```

---

## 🔌 API Endpoints

The API endpoints remain the same regardless of the underlying database.

### 1. Onboard User
Initiates the consent flow, fetches session data from Setu, and stores it in the database.

- **Endpoint**: `POST /api/user/onboard`
- **Body**:
  ```json
  {
    "mobileNumber": "9999999999",
    "consentId": "optional-consent-id" 
  }
  ```
- **Flow**:
  1.  Checks if a valid consent exists for the mobile number.
  2.  If not, creates a new Consent with Setu.
  3.  Creates a Data Session.
  4.  Fetches Account and Transaction data.
  5.  Stores User, Consent, Accounts, and Transactions in the configured database.

### 2. Get Transaction History
Retrieves stored transactions for a user.

- **Endpoint**: `GET /api/user/transactions`
- **Query Params**:
  - `mobileNumber`: The user's mobile number (Required)
  - `from`: Start date (Optional)
  - `to`: End date (Optional)
- **Example**: `/api/user/transactions?mobileNumber=9999999999`

---

## 🏗️ Architecture & Data Flow

The application uses the **Repository Pattern** to abstract the data storage layer.

1.  **Controller** (`UserController`): Receives HTTP requests.
2.  **Service** (`FiuClient`): Communicates with Setu APIs (Consent, Session, Data Fetch).
3.  **Repository Interface** (`IMongoRepository`): Defines the contract for data operations (Save Consent, Save Transactions, etc.).
4.  **Repository Implementation**:
    -   `MongoRepository`: Implements the interface using MongoDB Driver.
    -   `SqlRepository`: Implements the interface using Entity Framework Core (MySQL).
5.  **Database**: The configured database (Mongo or MySQL) stores the data.

### MySQL Schema Relationship
When using MySQL, the data is structured as follows:

-   **Users**: Identified by `MobileNumber`.
-   **Consents**: Linked to `Users`.
-   **Accounts**: Linked to `Users`.
-   **Transactions**: Linked to `Accounts`.

This ensures all data is aggregated under the user's mobile identity.
