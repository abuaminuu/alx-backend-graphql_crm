import graphene
# from graphene import relay
from graphene_django import DjangoObjectType
from .models import Student

class StudentType(DjangoObjectType):
    class Meta:
        model = Student
        filter_fields = {
            "registration_number":["itcontains"],
            "name":["itcontains"],
            "phone":["itcontains"],
        }

        interfaces = (graphene.relay.Node,)

        registration_number = graphene.String()
        def resolve_registration_number(self, info):
            return self.registration_number
        
        name = graphene.String()
        def resolve_name(self, info):
            return self.name

        phone = graphene.String()
        def resolve_name(self, info):
            return self.phone


class StudentQuery(graphene.ObjectType):
    student =  graphene.String()

    def resolve_student(self, info):
        return "student A"



schema = graphene.Schema(query=Query)
