import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(graphene.ObjectType):
    hello = graphene.String(default="Hello GraphQL")

    def resolve_hello(self, info):
        return f"hello, GraphQL!"

class Mutation(CRMMutation, graphene.ObjectType):
    pass


# create schema instance
schema = graphene.schema(query=Query, mutation=Mutation) 
