# 공부한 내용 2: gRPC 컨텍스트 제어

gRPC 컨텍스트는 요청의 생명주기를 제어하고, 메타데이터·압축·취소 같은 기능을 다루는 핵심 수단이다. 실습을 통해 긴 작업을 취소하거나 대량 데이터를 압축 전송하는 방법을 정리했다.

## 요청 취소 처리
- `context.is_active()`를 활용하면 서버에서 클라이언트가 연결을 유지 중인지 검사할 수 있다.
- 클라이언트는 `future = stub.LongRunningOperation.future(request)`로 비동기 호출 후 `future.cancel()`로 취소를 요청한다.
- 서버는 루프 내에서 컨텍스트를 확인하고, 요청이 취소되면 즉시 중단 응답을 반환한다.

```python
def LongRunningOperation(self, request, context):
    for step in range(10):
        if not context.is_active():
            return cancel_pb2.Response(response_data="Operation cancelled")
        time.sleep(1)
    return cancel_pb2.Response(response_data="Operation completed successfully")
```

## 전송 압축
- `grpc.server(..., compression=grpc.Compression.Gzip)`과 같이 서버·클라이언트 모두 압축 옵션을 설정해야 한다.
- 압축은 네트워크 비용을 줄이지만 CPU 사용량이 늘어날 수 있으므로 상황에 따라 조절한다.

```python
with grpc.insecure_channel(
    "localhost:50051",
    compression=grpc.Compression.Gzip,
) as channel:
    stub = data_service_pb2_grpc.DataServiceStub(channel)
    response = stub.GetData(data_service_pb2.DataRequest(data_id="test"))
```

## 정리 메모
- gRPC 컨텍스트는 단순한 요청 정보가 아니라 메타데이터, 취소, 데드라인, 압축 설정까지 모두 관리한다.
- 긴 작업에서는 컨텍스트를 주기적으로 확인해 빠르게 종료해야 리소스를 아낄 수 있다.
- 압축·타임아웃 등 통신 품질 설정을 통해 네트워크 환경에 맞춘 최적화가 가능하다.

## 코드 내용 전문

```proto
# cancel.proto
syntax = "proto3";

service CancelService {
    rpc LongRunningOperation (Request) returns (Response) {}
}

message Request {
    string request_data = 1;
}

message Response {
    string response_data = 1;
}
```

```python
# client.py
import grpc
import time
import cancel_pb2
import cancel_pb2_grpc

def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = cancel_pb2_grpc.CancelServiceStub(channel)
        request = cancel_pb2.Request(request_data="start")

        future = stub.LongRunningOperation.future(request)
        # time.sleep(3)
        # future.cancel()

        try:
            response = future.result()
            print(f"Response: {response.response_data}")
        except grpc.FutureCancelledError:
            print("Operation cancelled")


if __name__ == "__main__":
    run()
```

```python
# server.py
from concurrent import futures

import grpc
import time
import cancel_pb2
import cancel_pb2_grpc

class CancelService(cancel_pb2_grpc.CancelServiceServicer):
    def LongRunningOperation(self, request, context):
        for i in range(10):
            if context.is_active():
                print(f"Processing {i}...")
                time.sleep(1)
            else:
                print("Operatiorn cancelled")
                return cancel_pb2.Response(response_data="Operation cancelled")

        return cancel_pb2.Response(response_data="Operation completed successfully")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cancel_pb2_grpc.add_CancelServiceServicer_to_server(CancelService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

실행방법은 동일. 

## 데이터 압축방법

네트워크 대역폭을 줄이기 위해 압축을 사용하는데 네트워크 비용은 줄어들지만 압축하는데 서버의 계산량은 올라가게 됨. 트레이드오프가 있음

```proto
syntax = "proto3";

service DataService {
    rpc GetData (DataRequest) returns (DataResponse) {}
}

message DataRequest {
    string data_id = 1;
}

message DataResponse {
    bytes data = 1;
}
```

```python
#client.py

import grpc
import time

import data_service_pb2
import data_service_pb2_grpc

def run():
    with grpc.insecure_channel("localhost:50051", compression=grpc.Compression.Gzip) as channel:
        stub = data_service_pb2_grpc.DataServiceStub(channel)
        response = stub.GetData(data_service_pb2.DataRequest(data_id="test"))

        print(f"Data {len(response.data)} bytes")

if __name__ == "__main__":
    run()
```

```python
from concurrent import futures

import grpc
import time

import data_service_pb2
import data_service_pb2_grpc


class DataService(data_service_pb2_grpc.DataServiceServicer):
    def GetData(self, request, context):
        data_id = request.data_id

        data = b"This is a test data" * 100000

        print(f"Data {len(data)} bytes")

        return data_service_pb2.DataResponse(data=data)


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        compression=grpc.Compression.Gzip
    )

    data_service_pb2_grpc.add_DataServiceServicer_to_server(DataService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```