import argparse
import asyncio
import contextlib
from datetime import datetime, timezone

import grpc.aio

import chat_pb2
import chat_pb2_grpc


async def _read_input(queue: asyncio.Queue[str | None]) -> None:
    """Capture user input asynchronously and push it onto the queue."""
    try:
        while True:
            try:
                text = await asyncio.to_thread(input, "> ")
            except EOFError:
                break

            stripped = text.strip()
            if not stripped:
                continue

            await queue.put(stripped)
    except asyncio.CancelledError:
        raise
    finally:
        await queue.put(None)


async def _request_stream(username: str, queue: asyncio.Queue[str | None]):
    """Yield ClientEvent messages based on user input."""
    yield chat_pb2.ClientEvent(join=chat_pb2.JoinRequest(username=username))

    while True:
        payload = await queue.get()
        if payload is None:
            yield chat_pb2.ClientEvent(leave=chat_pb2.LeaveRequest(username=username))
            break
        yield chat_pb2.ClientEvent(message=chat_pb2.ChatInput(text=payload))


def _format_timestamp(timestamp) -> str:
    if not timestamp.seconds and not timestamp.nanos:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
    return timestamp.ToDatetime().astimezone().isoformat(timespec="seconds")


async def run_chat(username: str, host: str, port: int) -> None:
    target = f"{host}:{port}"
    outgoing: asyncio.Queue[str | None] = asyncio.Queue()
    input_task = asyncio.create_task(_read_input(outgoing))

    try:
        async with grpc.aio.insecure_channel(target) as channel:
            stub = chat_pb2_grpc.ChatServiceStub(channel)
            responses = stub.Chat(_request_stream(username, outgoing))

            print(f"Connected to chat server at {target} as '{username}'. Type messages and hit Enter.")
            async for message in responses:
                if message.system:
                    prefix = "[system]"
                else:
                    prefix = f"[{message.username}]"
                timestamp = _format_timestamp(message.sent_at)
                print(f"{timestamp} {prefix} {message.text}")
    except grpc.aio.AioRpcError as exc:
        print(f"Chat ended: {exc.code().name} - {exc.details()}")
    finally:
        input_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await input_task


def parse_args():
    parser = argparse.ArgumentParser(description="Async gRPC chat client")
    parser.add_argument("--username", "-u", default="anon", help="Display name in the chat room")
    parser.add_argument("--host", default="localhost", help="Chat server host")
    parser.add_argument("--port", type=int, default=50051, help="Chat server port")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    try:
        asyncio.run(run_chat(args.username, args.host, args.port))
    except KeyboardInterrupt:
        print("\nDisconnected.")

