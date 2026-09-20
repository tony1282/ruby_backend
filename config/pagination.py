from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound



class StandardPagination(PageNumberPagination):

    page_size = 50

    page_size_query_param = "page_size"

    max_page_size = 200
    
    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(
                queryset,
                request,
                view
            )
        except NotFound:
            raise NotFound("La página solicitada no es válida.")

    def get_paginated_response(self, data):

        return Response(
            {
                "success": True,
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "data": data,
            }
        )

    def get_paginated_response_schema(self, schema):

        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "count":   {"type": "integer"},
                "next":    {"type": "string", "nullable": True},
                "previous":{"type": "string", "nullable": True},
                "data":    schema,
            },
        }
