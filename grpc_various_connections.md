

## Timeout 과 Wait 설정

```proto

syntax = "proto3";

service EchoService {
    rpc Echo (EchoRequest) returns (EchoResponse) {}
}

message EchoRequest {
    string echo_message = 1;
}

message EchoResponse {
    string echo_message = 1;
}
```

```python
# server.py

from concurrent import futures
import wait_example_pb2
import wait_example_pb2_grpc
import time
import grpc

keep_alive_options = [
    ("grpc.keepalive.time_ms", 10000),
    ("grpc.keepalive.timeout_ms", 5000),
    ("grpc.keepalive.permit_without_calls", 1)
]


class EchoService(wait_example_pb2_grpc.EchoServiceServicer):
    def Echo(self, request, context):
        time.sleep(2)
        return wait_example_pb2.EchoResponse(echo_message=request.echo_message)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options=keep_alive_options)
    wait_example_pb2_grpc.add_EchoServiceServicer_to_server(EchoService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

```python
# client.py

import grpc
import time

import wait_example_pb2
import wait_example_pb2_grpc

keep_alive_options = [
    ("grpc.keepalive.time_ms", 10000),
    ("grpc.keepalive.timeout_ms", 5000),
    ("grpc.keepalive.permit_without_calls", 1)
]

def run():
    with grpc.insecure_channel("localhost:50051", options=keep_alive_options) as channel:
        stub = wait_example_pb2_grpc.EchoServiceStub(channel)

        try:
            response = stub.Echo(wait_example_pb2.EchoRequest(echo_message="Hello, gRPC!"), timeout=1)
            print(f"Response: {response.echo_message}")
        except grpc.RpcError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    run()
```


## metadata

```proto

syntax = "proto3";

service EchoService {
    rpc Echo (EchoRequest) returns (EchoResponse) {}
}

message EchoRequest {
    string echo_message = 1;
}

message EchoResponse {
    string echo_message = 1;
}
```

```python
#server.py

from concurrent import futures
import meta_example_pb2
import meta_example_pb2_grpc
import time
import grpc

class EchoService(meta_example_pb2_grpc.EchoServiceServicer):
    def Echo(self, request, context):
        metadata = dict(context.invocation_metadata())
        print(f"Metadata: {metadata}s")

        context.set_trailing_metadata((("custom-header", "value"),))

        return meta_example_pb2.EchoResponse(echo_message=request.echo_message)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    meta_example_pb2_grpc.add_EchoServiceServicer_to_server(EchoService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

```python
# client.py

import grpc
import time

import meta_example_pb2
import meta_example_pb2_grpc


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = meta_example_pb2_grpc.EchoServiceStub(channel)

        try:
            metadata = [("client-custom-header", "client-value")]
            response, call = stub.Echo.with_call(meta_example_pb2.EchoRequest(echo_message="Hello, gRPC!"),metadata=metadata)
            print(f"Response: {response.echo_message}")

            # Server metadata
            server_metadata = dict(call.trailing_metadata())
            print(f"Server metadata: {server_metadata}")

        except grpc.RpcError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    run()
```


## Authorization

### Basic Authorization

TLS 인증이 필요.

1. HTTP의 Header에 Base64로 인코딩된 사용자 이름과 비밀번호를 포함하여 전송
2. 서버는 context에서 해당 헤더를 추출해 인증 절차를 진행한다. 

### Session Authorization

상태유지의 장점이 있으며, 서버에 해당 세션의 상태를 저장해야 하는 단점이 있다.

1. 클라이언트가 처음 서버에 클라이언트의 이름과 비밀번호를 보내 인증 요청
2. 서버는 해당 계정정보를 검증한다. 
3. 서버는 해당 클라이언트에 대해 세션ID을 생성 후, 세션ID를 클라이언트에게 반환. 
4. 클라이언트는 이후 이 세션ID를 포함시켜 서버에 인증

### Token Authorization

서버에 별도 저장필요 없이 토큰만 가지고있으면 통신가능, 대신 토큰이 유출되면 위험.

1. 클라이언트가 처음 서버에 클라이언트의 이름과 비밀번호를 보내 인증 요청
2. 서버는 해당 계정정보를 검증한다. 
3. 서버는 해당 클라이언트에 대해 JWT와 같은 토큰을 발행한 후, 토큰을 클라이언트에게 반환. 
4. 클라이언트는 이후 이 토큰을 포함시켜 서버에 인증

### TLS 인증 예제

#### 키 발급

```bash
# private key
openssl genpkey -algorithm RSA -out server.key
# -> 열쇠와 같은 공개되면 안되는 key

# 인증서 서명 요청(CSR) 생성
openssl req -new -key server.key -out server.csr
# -> 자신의 공개키와 인증서에 넣을 식별정보와 함께 CA에 서명 요청을 보내는 문서
# -> .pub과 비슷한 느낌 공개되어도 상관없고, 개인키와 페어링되어있음
# Common Name: localhost 입력필요!

# 자체 서명된 인증서 생성
openssl x509 -req -in server.csr -signkey server.key -out server.crt -days 365
# -> 서버가 개인키로 직접 csr을 서명해서 만든 인증서
```

```proto

syntax = "proto3";

service ExampleService {
    rpc SayHello (HelloRequest) returns (HelloReply) {}
}

message HelloRequest {
    string name = 1;
}

message HelloReply {
    string reply_message = 1;
}
```

```python
#server.py

from concurrent import futures
from doctest import Example
import auth_example_pb2
import auth_example_pb2_grpc
import time
import grpc


class ExampleService(auth_example_pb2_grpc.ExampleServiceServicer):
    def SayHello(self, request, context):
        response = auth_example_pb2.HelloReply()
        response.reply_message = f"Hello, {request.name}!"

        return response


def serve():
    with open("server.key", "rb") as key:
        private_key = key.read()
    with open("server.crt", "rb") as cert:
        certificate = cert.read()
    
    credentials = grpc.ssl_server_credentials(
        ((private_key, certificate),)
    )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_example_pb2_grpc.add_ExampleServiceServicer_to_server(ExampleService(), server)

    server.add_secure_port("[::]:50051", credentials)
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

```python
# client.py

import grpc
import time

import auth_example_pb2
import auth_example_pb2_grpc

def run():
    with open("server.crt", "rb") as cert:
        certificate = cert.read()

    credentials = grpc.ssl_channel_credentials(certificate)

    with grpc.secure_channel("localhost:50051", credentials) as channel:
        stub = auth_example_pb2_grpc.ExampleServiceStub(channel)
        response = stub.SayHello(auth_example_pb2.HelloRequest(name="Hyeonghwan"))
        print(f"Greeting Response: {response.reply_message}")

if __name__ == "__main__":
    run()
```

## Retry

```proto

syntax = "proto3";

service ExampleService {
    rpc SayHello (HelloRequest) returns (HelloReply) {}
}

message HelloRequest {
    string name = 1;
}

message HelloReply {
    string reply_message = 1;
}
```

```python
#server.py

from concurrent import futures

import retry_example_pb2
import retry_example_pb2_grpc

import time
import grpc


class ExampleService(retry_example_pb2_grpc.ExampleServiceServicer):
    def SayHello(self, request, context):
        if time.time() % 2 < 1:
            print("Server Unavailable")
            context.abort(grpc.StatusCode.UNAVAILABLE, "Server Unavailable")
        
        return retry_example_pb2.HelloReply(reply_message=f"Hello, {request.name}!")


def serve():

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    retry_example_pb2_grpc.add_ExampleServiceServicer_to_server(ExampleService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

```python
# client.py

import grpc
import time
import json

import retry_example_pb2
import retry_example_pb2_grpc

# gRPC 재시도 정책 딕셔너리
# gRPC 서비스 재시도 정책(service config) 설정
service_config = {
    "methodConfig": [{
        "name": [{}],  # 서비스 내 모든 메서드에 대해 적용
        "retryPolicy": {
            "maxAttempts": 10,                # 최대 재시도 횟수
            "initialBackoff": "0.1s",        # 첫 재시도까지 대기 시간
            "maxBackoff": "1s",              # 최대 대기 시간
            "backoffMultiplier": 2.0,        # 재시도 시 backoff 계수 (지수 증가)
            "retryableStatusCodes": ["UNAVAILABLE"]  # 재시도할 오류 코드 목록
        }
    }]
}

channel_options = [
    ("grpc.enable_retries", 1),
    ("grpc.service_config", json.dumps(service_config))
]

def run():
    with grpc.insecure_channel("localhost:50051", options=channel_options) as channel:
        stub = retry_example_pb2_grpc.ExampleServiceStub(channel)

        try:
            response = stub.SayHello(retry_example_pb2.HelloRequest(name="Hyeonghwan"))
            print(f"Received: {response.reply_message}")
        except grpc.RpcError as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run()
```



 










