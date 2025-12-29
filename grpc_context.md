
# gRPC Context Control

## gRPC 요청 취소

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


## gRPC Interceptor



