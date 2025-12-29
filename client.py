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