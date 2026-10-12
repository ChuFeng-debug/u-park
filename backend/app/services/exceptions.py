"""Erreurs métier levées par la couche services.

Les routes n'ont pas à les intercepter : un gestionnaire global
(voir `app.main`) les convertit en réponse HTTP avec le bon code.
"""


class ServiceError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class InvalidRequestError(ServiceError):
    status_code = 400


class AccessDeniedError(ServiceError):
    status_code = 403


class NotFoundError(ServiceError):
    status_code = 404


class ConflictError(ServiceError):
    status_code = 409
