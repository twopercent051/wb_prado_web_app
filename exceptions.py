from fastapi import HTTPException, status


class AppException(HTTPException):
    status_code = 500
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class IncorrectLoginOrPasswordException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Неверный логин или пароль"


class JWTIsFailException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Токен невалидный"
