"""Kafka async messaging adapter."""
from __future__ import annotations

import json

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import structlog

from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)


class KafkaProducer:
    def __init__(self):
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def publish(self, topic: str, message: dict, key: str | None = None) -> None:
        if not self._producer:
            raise RuntimeError("KafkaProducer not started")
        key_bytes = key.encode("utf-8") if key else None
        await self._producer.send_and_wait(topic, value=message, key=key_bytes)
        logger.debug("kafka_message_published", topic=topic, key=key)


class KafkaConsumer:
    def __init__(self, topics: list[str], group_id: str):
        self._consumer: AIOKafkaConsumer | None = None
        self._topics = topics
        self._group_id = group_id

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        await self._consumer.start()

    async def stop(self) -> None:
        if self._consumer:
            await self._consumer.stop()

    async def __aiter__(self):
        if not self._consumer:
            raise RuntimeError("KafkaConsumer not started")
        async for msg in self._consumer:
            yield msg
