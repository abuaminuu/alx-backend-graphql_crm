import graphene
import crm.schema
import maahad.schema



class Query(graphene.ObjectType):

    hello = graphene.String(default_value="hello gQL!")
    def resolve_hello(self, info):
        acc = "CSJ-5648"
        return f"hello, GraphQL! {acc}"

    name = graphene.String(default_value="Name...")
    def resolve_name(self, info):
        return f"i am xyx! by name"
    
    number = graphene.String(default_value="+323")
    def resolve_number(self, info):
        return f"+1234213412J"

# create schema instance
schema = graphene.Schema(query=Query)
