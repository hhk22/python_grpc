
# gRPC 통신 기법 4가지

## Unary RPC

클라이언트가 서버에 요청을 보내고, 서버가 클라이언트에 한번 응답하는 교환 방식. 

HTTP와 Request-Reponse 모델과 매우 유사

### 장단점

오버헤드가 적은편이고 직관적이지만, 제한된 데이터 전송이라 gRPC의 장점을 살리는 방식은 아님. 

### Basic Usage

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