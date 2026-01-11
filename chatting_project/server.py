import asyncio
import contextlib
import logging
import uuid
from datetime import datetime, timezone

import grpc.aio
from google.protobuf.timestamp_pb2 import Timestamp

import chat_pb2
import chat_pb2_grpc


def _utc_timestamp():
    """Return a Timestamp set to the current UTC time."""
    ts = Timestamp()
    ts.FromDatetime(datetime.now(timezone.utc))
    return ts


class ChatRoom:
    """Shared state for broadcasting messages to connected clients."""

    def __init__(self):
        self._clients: dict[str, asyncio.Queue[chat_pb2.ChatMessage]] = {}
        self._lock = asyncio.Lock()

    async def register(self, connection_id: str, queue: asyncio.Queue, username: str) -> None:
        async with self._lock:
            self._clients[connection_id] = queue
        await self.broadcast(
            chat_pb2.ChatMessage(
                username="system",
                text=f"{username} joined the chat",
                sent_at=_utc_timestamp(),
                system=True,
            )
        )

    async def unregister(self, connection_id: str, username: str | None) -> None:
        async with self._lock:
            self._clients.pop(connection_id, None)
        if username:
            await self.broadcast(
                chat_pb2.ChatMessage(
                    username="system",
                    text=f"{username} left the chat",
                    sent_at=_utc_timestamp(),
                    system=True,
                ),
                exclude=connection_id,
            )

    async def broadcast(
        self,
        message: chat_pb2.ChatMessage,
        *,
        exclude: str | None = None,
    ) -> None:
        async with self._lock:
            targets = [
                queue
                for conn_id, queue in self._clients.items()
                if conn_id != exclude
            ]

        if not targets:
            return

        await asyncio.gather(*(queue.put(message) for queue in targets), return_exceptions=True)


class ChatService(chat_pb2_grpc.ChatServiceServicer):
    """Bidirectional streaming gRPC chat service implemented with asyncio."""

    def __init__(self, room: ChatRoom):
        self._room = room

    async def Chat(self, request_iterator, context):
        connection_id = f"{context.peer()}-{uuid.uuid4().hex[:6]}"
        outgoing_queue: asyncio.Queue[chat_pb2.ChatMessage] = asyncio.Queue(maxsize=100)
        username: str | None = None

        async def consume_requests():
            nonlocal username
            try:
                async for event in request_iterator:
                    if event.HasField("join"):
                        if username:
                            logging.warning("Duplicate join attempt from %s", connection_id)
                            continue
                        provided_name = event.join.username.strip()
                        username = provided_name or f"guest-{uuid.uuid4().hex[:4]}"
                        await self._room.register(connection_id, outgoing_queue, username)
                    elif event.HasField("message"):
                        if not username:
                            logging.warning("Client %s attempted to chat before joining", connection_id)
                            continue
                        message = chat_pb2.ChatMessage(
                            username=username,
                            text=event.message.text,
                            sent_at=_utc_timestamp(),
                            system=False,
                        )
                        await self._room.broadcast(message)
                    elif event.HasField("leave"):
                        logging.info("Client %s requested to leave", connection_id)
                        break
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logging.exception("Error consuming client events: %s", exc)
            finally:
                await self._room.unregister(connection_id, username)
                # Wake up the generator loop so that the stream closes cleanly.
                await outgoing_queue.put(
                    chat_pb2.ChatMessage(
                        username="system",
                        text="",
                        sent_at=_utc_timestamp(),
                        system=True,
                    )
                )

        consumer_task = asyncio.create_task(consume_requests())

        try:
            while True:
                message = await outgoing_queue.get()
                if message.text == "" and message.username == "system" and message.system:
                    # Sentinel used to close the stream without sending extra data.
                    break
                yield message
        except asyncio.CancelledError:
            raise
        finally:
            consumer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await consumer_task


async def serve(host: str = "[::]", port: int = 50051) -> None:
    server = grpc.aio.server()
    room = ChatRoom()
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(room), server)
    server.add_insecure_port(f"{host}:{port}")

    logging.info("Starting chat server on %s:%s", host, port)
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())

