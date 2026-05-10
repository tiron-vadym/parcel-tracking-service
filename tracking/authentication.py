from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """
    Swagger UI handles HTTP Bearer auth ergonomically: user enters only token value,
    and client sends `Authorization: Bearer <token>`.
    """

    keyword = "Bearer"
