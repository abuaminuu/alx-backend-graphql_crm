# test_graphql_query.py
import requests
import json

query = """
{
  allOrders(where: {status: "pending"}, first: 5) {
    edges {
      node {
        id
        orderDate
        customer {
          name
          email
        }
      }
    }
  }
}
"""

response = requests.post(
    "http://localhost:8000/graphql",
    json={"query": query},
    headers={"Content-Type": "application/json"}
)

print("Status Code:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))
