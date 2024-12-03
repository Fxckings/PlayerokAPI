"""
В данном модуле описаны все кастомные исключения, используемые в пакете PlayerokAPI.
"""

class StatusCodeError(Exception):
    """
    Исключение, которое выбрасывается при некорректном статус-коде ответа.
    """
    def __init__(self, status_code, message=None):
        self.status_code = status_code
        self.message = message or "Некорректный статус-код ответа."

    def __str__(self):
        """
        Возвращает строковое представление исключения.

        :return: Строка, описывающая исключение.
        """
        return f"{self.message} (Статус-код: {self.status_code})"