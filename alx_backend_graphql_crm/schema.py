import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="hello gQL!")
    

    def resolve_hello(self, info):
        acc = "CSX-5648"
        return f"hello, GraphQL! {acc}"

    name = graphene.String(default_value="Name...")
    
    def resolve_name(self, info):
        return f"i am xyx by name"


# create schema instance
schema = graphene.Schema(query=Query)
