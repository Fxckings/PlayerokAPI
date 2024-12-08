from __future__ import annotations

import uuid
from faker import Faker
from typing import Dict

class RequestsModel:
    """
    Базовый класс для моделей запросов.
    """
    def __init__(self):
        self.faker = Faker()

    def generate_random_baggage(self) -> str:
        release = self.faker.sha1()[:12]
        public_key = self.faker.sha1()
        trace_id = uuid.uuid4()
        environment = self.faker.random_element(elements=("production", "staging", "development"))
        transaction = "/".join(
            (
                self.faker.random_element(elements=("profile", "search", "chat")),
                self.faker.random_element(elements=("products", "item", "user")),
                self.faker.random_element(elements=("products", "item", "user")),
            )
        )
        sample_rate = round(self.faker.pydecimal(left_digits=2, right_digits=4, positive=True), 4)
        sampled = self.faker.boolean()
        return (
            f"sentry-environment={environment},"
            f"sentry-release={release},"
            f"sentry-public_key={public_key},"
            f"sentry-trace_id={trace_id},"
            f"sentry-sample_rate={sample_rate},"
            f"sentry-transaction={transaction},"
            f"sentry-sampled={sampled}"
        )

    def generate_headers(self) -> Dict[str, str]:
        """
        Генерирует дефолтные заголовки для запросов, которые позволяют обойти клаудфлейр.
        
        Returns:
            Dict: Рандомные заголовки.
        """
        return {
            "User-Agent": self.faker.user_agent(),
            "Accept": "*/*",
            "Accept-Language": f"{self.faker.locale()}",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/json",
            "Apollo-Require-Preflight": f"{self.faker.boolean()}",
            "Access-Control-Allow-Headers": "sentry-trace, baggage",
            "Apollographql-Client-Name": self.faker.random_element(elements=["web", "mobile", "desktop"]),
            "X-Timezone-Offset": f"{self.faker.pyint(min_value=-720, max_value=720)}",
            "Sentry-Trace": f"{uuid.uuid4()}-{uuid.uuid4()}-0",
            "Baggage": self.generate_random_baggage(),
            "Origin": "https://playerok.com",
            "DNT": f"{self.faker.pyint(min_value=0, max_value=1)}",
            "referer": f"{self.faker.uri()}",
            "Sec-GPC": f"{self.faker.pyint(min_value=0, max_value=1)}",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": self.faker.random_element(elements=["document", "embed", "empty", "object", "iframe", "audio", "video", "track", "report"]),
            "Sec-Fetch-Mode": self.faker.random_element(elements=["navigate", "no-cors", "same-origin", "cors"]),
            "Sec-Fetch-Site": self.faker.random_element(elements=["cross-site", "same-origin", "same-site", "none"]),
        }

    def generate_impersonate(self) -> str:
        """
        Генерирует рандом версию браузера хромчик.

        Returns:
            str: Рандом версия браузера.
        """
        return self.faker.random_element(elements=[
            "chrome116", "chrome119"
        ])