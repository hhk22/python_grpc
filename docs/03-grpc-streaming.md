# 공부한 내용 3: gRPC 스트리밍 패턴

gRPC는 네 가지 통신 패턴을 제공한다. 각각의 장단점과 기본 구현 패턴을 실습으로 정리했다.

## 1. Unary RPC
- 요청 1건에 응답 1건을 주고받는 가장 단순한 형태.
- HTTP API와 유사해 이해하기 쉽고 오버헤드가 적지만, 스트리밍이 제공하는 장점을 살리기 어렵다.
- `stub.SayHello(HelloRequest(name="Hyeonghwan"))`처럼 호출하며 결과는 즉시 반환된다.

## 2. Server Streaming
- 클라이언트가 하나의 요청을 보내고, 서버가 스트림 형태로 여러 메시지를 푸시한다.
- 예: 공지 방송, 파일 다운로드 진행 업데이트 등.
- 구현 팁: 서버에서 `yield`로 메시지를 순차 전송하고, 클라이언트는 `for message in stub.ChatStream(...)`처럼 반복문으로 소비한다.

## 3. Client Streaming
- 클라이언트가 여러 메시지를 연속 전송한 뒤 서버의 단일 응답을 받는다.
- 예: 대량 업로드, 센서 데이터 배치 전송.
- 클라이언트는 제너레이터로 메시지를 보내고, 서버는 요청 이터레이터를 순회해 집계 후 응답한다.

## 4. Bidirectional Streaming
- 클라이언트와 서버가 동시에 스트림을 주고받는 가장 강력한 패턴.
- 실시간 채팅, 공동 편집, 스트리밍 분석 등에 적합하다.
- 양쪽 모두 비동기 루프에서 `yield`와 `async for`를 조합해 메시지를 처리하며, 흐름 제어와 예외 처리가 중요하다.

## 요약 메모
- 스트리밍을 활용하면 실시간 데이터 흐름을 자연스럽게 구성할 수 있다.
- 각 패턴은 사용 시점이 다르므로 요구사항에 맞춰 선택해야 한다.
- Python gRPC에서는 제너레이터와 async/await를 적극적으로 활용해 구조를 단순화할 수 있다.

## 코드 내용 전문

```proto
# hello_world.proto
syntax = "proto3";

service Greeter {
    rpc SayHello (HelloRequest) returns (HelloResponse) {}
}

message HelloRequest {
    string name = 1;
}

message HelloResponse {
    string response_text = 1;
}
```

```python
# client.py
import grpc
import hello_world_pb2
import hello_world_pb2_grpc

def run():
    with grpc.insecure_channel("localhost:50051") as channel
        stub = hello_world_pb2_grpc.GreeterStub(channel)
        response = stub.SayHello(hello_world_pb2.HelloRequest(name="Hyeonghwan"))
        print(response.response_text)

if __name__ == "__main__":
    run()
```

```python
# server.py
from concurrent import futures

import grpc
import hello_world_pb2
import hello_world_pb2_grpc

class Greeter(hello_world_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return hello_world_pb2.HelloResponse(response_text=f"Hello, {request.name}!")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hello_world_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

```shell
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. hello_world.proto

# terminal I
python server.py

# terminal II
python client.py
>> Hello, Hyeonghwan!
```

## Server-Client, Client-Server Streaming

- `server streaming` 은 하나의 요청과 여러개의 응답.
- `client streaming` 은 여러개의 요청과 하나의 응답.

많은 데이터를 실시간으로 효과적으로 전송이 가능하지만 전송이 끝날때까지 기다려야한다는 단점. 

### Server Streaming Basic Usage

```proto
# messages.proto
syntax = "proto3";

service ChatService {
    rpc ChatStream (ChatMessage) returns (stream ChatMessage) {}
}

message ChatMessage {
    string message_text = 1;
}
```

```python
# client.py

import grpc
import messages_pb2
import messages_pb2_grpc

def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = messages_pb2_grpc.ChatServiceStub(channel)

        for message in stub.ChatStream(messages_pb2.ChatMessage(message_text="start")):
            print(f"Received message: {message.message_text}")

if __name__ == "__main__":
    run()
```

```python
# server.py

from concurrent import futures

import grpc
import time
import messages_pb2
import messages_pb2_grpc

class ChatService(messages_pb2_grpc.ChatServiceServicer):
    def ChatStream(self, request, context):
        messages = [
            "Hello world",
            "This is server streaming grpc",
            "Good bye"
        ]

        for message in messages:
            yield messages_pb2.ChatMessage(message_text=message)
            time.sleep(1)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

```

```shell
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. messages.proto

# terminal I
python server.py

# terminal II
python client.py
>>
Received message: Hello world
Received message: This is server streaming grpc
Received message: Good bye
```

### Client Streaming Basic Usage

```proto
syntax = "proto3";

service ChatService {
    rpc ChatStream (stream ChatMessage) returns (ChatMessage) {}
}

message ChatMessage {
    string message_text = 1;
}
```

```python
# server.py
from concurrent import futures

import grpc
import time
import messages_pb2
import messages_pb2_grpc

class ChatService(messages_pb2_grpc.ChatServiceServicer):
    def ChatStream(self, request_iterator, context):
        result = ""
        for message in request_iterator:
            result += message.message_text + " "
        
        return messages_pb2.ChatMessage(message_text=result)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

```python
# client.py
import grpc
import messages_pb2
import messages_pb2_grpc

def generate_messages():
    messages = ["msg1", "msg2", "msg3"] 
    for msg in messages:
        yield messages_pb2.ChatMessage(message_text=msg)

def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = messages_pb2_grpc.ChatServiceStub(channel)
        response = stub.ChatStream(generate_messages())
        print(response.message_text)

if __name__ == "__main__":
    run()
```

```shell
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. messages.proto

# Terminal I
python server.py

# Terminal II
python client.py
>>
msg1 msg2 msg3
```

## Bidirectional Streaming RPC

클라이언트와 서버가 서로 **스트림** 형태로 데이터를 주고받는 방식. 
-> 가장 RPC의 성격을 잘 활용하는 방식. 

실시간 데이터 전송가능, 상호작용이 가능하지만 구현이 복잡하다는것이 단점. 


### Basic Usage

```proto
# messages.proto
syntax = "proto3";

service ChatService {
    rpc Chat (stream ChatMessage) returns (stream ChatMessage) {}
}

message ChatMessage {
    string message_text = 1;
}
```

```python
# client.py

import grpc
import time
import messages_pb2
import messages_pb2_grpc

def generate_messages():
    messages = [
        "Hello grpc!",
        "This is Bidirectional Streaming RPC!",
        "Is it working good?"
    ]

    for msg in messages:
        print(f"Client Message: {msg}")
        yield messages_pb2.ChatMessage(message_text=msg)
        time.sleep(2)


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = messages_pb2_grpc.ChatServiceStub(channel)
        response = stub.Chat(generate_messages())

        for res in response:
            print(f"Received message: {res.message_text}")



if __name__ == "__main__":
    run()
```

```python
# server.py

from concurrent import futures

import grpc
import time
import messages_pb2
import messages_pb2_grpc

class ChatService(messages_pb2_grpc.ChatServiceServicer):
    def Chat(self, request_iterator, context):
        for message in request_iterator:
            print(f"Client Message: {message.message_text}")
            received_message = messages_pb2.ChatMessage(message_text=f"Received: {message.message_text}")
            yield received_message
            time.sleep(1)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messages_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

```shell
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. messages.proto

# Terminal I
python server.py
>> (Terminal II에서 python client.py를 치면)
Client Message: Hello grpc!
Client Message: This is Bidirectional Streaming RPC!
Client Message: Is it working good?

# Terminal II
python client.py
>>
Client Message: Hello grpc!
Received message: Received: Hello grpc!
Client Message: This is Bidirectional Streaming RPC!
Received message: Received: This is Bidirectional Streaming RPC!
Client Message: Is it working good?
Received message: Received: Is it working good?
```