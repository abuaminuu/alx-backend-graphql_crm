# 1. Create a single customer
mutation {
  createCustomer(input: {
    name: "John Doe",
    email: "john@example.com",
    phone: "+1234567890"
  }) {
    customer {
      id
      name
      email
      phone
    }
    message
  }
}

# 2. Bulk create customers
mutation {
  bulkCreateCustomers(inputs: [
    {name: "Alice", email: "alice@example.com", phone: "123-456-7890"},
    {name: "Bob", email: "bob@example.com"},
    {name: "Charlie", email: "charlie@example.com", phone: "+447123456789"}
  ]) {
    customers {
      id
      name
      email
    }
    errors
  }
}

# 3. Create a product
mutation {
  createProduct(input: {
    name: "Laptop",
    price: 999.99,
    stock: 10
  }) {
    product {
      id
      name
      price
      stock
    }
  }
}

# 4. Create an order
mutation {
  createOrder(input: {
    customerId: "customer-uuid-here",
    productIds: ["product-uuid-1", "product-uuid-2"]
  }) {
    order {
      id
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

# 5. Query all customers
query {
  allCustomers {
    edges {
      node {
        id
        name
        email
        phone
        orders {
          edges {
            node {
              id
              totalAmount
            }
          }
        }
      }
    }
  }
}
