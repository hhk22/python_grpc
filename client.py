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