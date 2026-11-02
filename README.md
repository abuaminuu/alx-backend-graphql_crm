# ALX Backend GraphQL CRM API

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2%2B-092E20?style=for-the-badge&logo=django&logoColor=white)
![GraphQL](https://img.shields.io/badge/GraphQL-Graphene-E10098?style=for-the-badge&logo=graphql&logoColor=white)

A robust, enterprise-ready GraphQL API built with **Django** and **Graphene-Django**. This project provides scalable CRM functionalities, featuring flexible queries, nested mutations, bulk operations with partial success handling, strict data validation, and real-time execution via GraphiQL.

---

## 🛠️ Stack & Dependencies

- **Framework:** Django 4.x / Django ORM
- **GraphQL Engine:** `graphene-django`
- **Filtering & Utilities:** `django-filter`
- **API Testing:** GraphiQL UI, Insomnia, Postman

---

## 📁 Repository & File Structure

```text
alx-backend-graphql_crm/
├── alx_backend_graphql_crm/
│   ├── settings.py
│   ├── urls.py
│   └── schema.py          # Root Schema combining Query & Mutation
├── crm/
│   ├── models.py          # Customer, Product, and Order models
│   ├── schema.py          # App-specific GraphQL Queries & Mutations
│   └── apps.py
└── manage.py
```

---

## 🚀 Quickstart & Setup

### 1. Environment Setup

Clone the repository and install the required dependencies:

```bash
# Clone the repository
git clone https://github.com/your-username/alx-backend-graphql_crm.git
cd alx-backend-graphql_crm

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django graphene-django django-filter
```

### 2. Database Migrations

Apply standard Django ORM migrations to set up your database schema:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Run Development Server

Start the Django development server:

```bash
python manage.py runserver
```

Navigate to **`http://localhost:8000/graphql`** to launch the interactive GraphiQL interface.

---

## 🧪 GraphQL Testing & Usage Guide

### Task 0: GraphQL Endpoint Checkpoint

#### Query
```graphql
query HealthCheck {
  hello
}
```

#### Expected Output
```json
{
  "data": {
    "hello": "Hello, GraphQL!"
  }
}
```

---

### Task 1: CRM Operations & Mutations

#### 1. Single Customer Creation
Creates a single customer record with strict email uniqueness and phone format validation.

```graphql
mutation CreateCustomer {
  createCustomer(
    name: "Jane Doe",
    email: "jane.doe@example.com",
    phone: "+1234567890"
  ) {
    customer {
      id
      name
      email
      phone
    }
    message
  }
}
```

#### 2. Bulk Customer Creation (Partial Success Support)
Allows creating multiple customer records in a single execution. Valid entries are created even if individual records fail validation.

```graphql
mutation BulkCreateCustomers {
  bulkCreateCustomers(
    customers: [
      { name: "Alice Smith", email: "alice@example.com", phone: "+1987654321" },
      { name: "Bob Johnson", email: "invalid-email-format", phone: "123" },
      { name: "Charlie Brown", email: "charlie@example.com" }
    ]
  ) {
    createdCustomers {
      id
      name
      email
    }
    errors {
      index
      error
    }
  }
}
```

#### 3. Product Creation
Adds a product with positive price validation and default stock enforcement.

```graphql
mutation CreateProduct {
  createProduct(
    name: "Enterprise Wireless Mouse",
    price: 49.99,
    stock: 150
  ) {
    product {
      id
      name
      price
      stock
    }
  }
}
```

#### 4. Nested Order Creation
Creates an order associated with an existing customer and array of products, automatically calculating the order total amount.

```graphql
mutation CreateOrder {
  createOrder(
    customerId: "1",
    productIds: ["1", "2"]
  ) {
    order {
      id
      orderDate
      totalAmount
      customer {
        name
        email
      }
      products {
        name
        price
      }
    }
  }
}
```

---

## 🔒 Validation Rules & Safeguards

- **Email Uniqueness & Format:** Validated on model/mutation level before saving.
- **Price & Stock Standards:** Prices must be strictly positive (`price > 0`); stock values cannot be negative (`stock >= 0`).
- **Relational Integrity:** Orders verify customer and product ID existence prior to execution and require at least one valid product.

---

## 🤝 Contributing

1. Fork the project repository.
2. Create your feature branch (`git checkout -b feature/NewGraphQLFeature`).
3. Commit your changes (`git commit -m 'Add new GraphQL feature'`).
4. Push to the branch (`git push origin feature/NewGraphQLFeature`).
5. Open a Pull Request.