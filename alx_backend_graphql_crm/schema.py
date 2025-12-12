# graphql_crm/schema.py
import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(CRMQuery, graphene.ObjectType):
    # You can add more queries from other apps here
    # Example: from auth.schema import Query as AuthQuery
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    # You can add more mutations from other apps here
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
