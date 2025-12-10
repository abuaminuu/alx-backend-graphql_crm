import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(default="Hello GraphQL")

    def resolve_hello(self, info):
        return f"hello, GraphQL!"

# create schema instance
schema = graphene.schema(query=Query) 
