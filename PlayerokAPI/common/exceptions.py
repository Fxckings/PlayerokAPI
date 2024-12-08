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
        return f"Ошибка при запросе: {self.message} (Статус-код: {self.status_code})"
    
class MaxRetryError(Exception):
    """
    Исключение, которое выбрасывается при достижении максимального количества попыток кинуть запрос.
    """
    def __init__(self, max_retries):
        self.max_retries = max_retries

    def __str__(self):
        return f"Достигнуто максимальное количество попыток ({self.max_retries})"

class RunnerError(Exception):
    """
    Исключение, которое выбрасывается при ошибки в ранере.
    """
    def __init__(self, message=None):
        self.message = message or "Произошла ошибка в ранере. Ничего старшного, если сообщение появляется нечасто."
    
    def __str__(self) -> str:
        return f"Произошла ошибка в ранере: {self.message}"
    
class NotJsonResponseError(Exception):
    """
    Исключение, которое выбрасывается при некорректном ответе в формате JSON.
    """
    def __init__(self, message=None):
        self.message = message or "Ответ не в формате JSON."

    def __str__(self):
        return f"Ответ не в формате JSON: {self.message}"
    
class CloudflareError(Exception):
    """
    Исключение, которое выбрасывается при ошибке с обходом Cloudflare.
    """
    def __init__(self, message=None):
        self.message = message or "Не удалось обойти Cloudflare."
    
    def __str__(self):
        return f"Произошла ошибка с обходом Cloudflare. Меняю хедеры к запросам. Текст ошибки: {self.message}"