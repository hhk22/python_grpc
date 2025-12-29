
# gRPC

- HTTP/2
- Protocol Buffers (protobuf)
- 

# Installation

```bash

conda create --name grpc-python python=3.12
conda activate grpc-python
pip install grpcio grpcio-tools

# Test
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. test.proto
>> test_pb.py, test_pb2_grpc.py 파일이 생성되야함. 

```

# Explaination

## Protocol Buffers

데이터 직렬화 매커니즘인데, 단순히 직렬화만 하는것이 아니라 메세지와 서비스를 정의하고, 언어에 맞는 서버와 클라이언트코드를 자동으로 생성할 수 있다. 

하나의 proto 파일로 go, python 코드를 생성할 수 있어서 에러가능성을 줄일 수 있음!

바이너리 형식이라 빠르고 효율적!

### Basic Usage


```proto
# book.proto
syntax = "proto3";

message Book {
    string book = 1;
    string author = 2;
    string publisher = 3;
    string customer = 4;
    int32  order = 5;
}
```

```python
# test.py
import book_pb2

book = book_pb2.Book()
book.book = "The Great Gatsby"
book.author = "F. Scott Fitzgerald"
print(book)

# Serialization
serialized_book = book.SerializeToString()
print(serialized_book)  # binary

# Deserialization
book = book_pb2.Book()
book.ParseFromString(serialized_book)
print(book)
```

```shell
#shell script
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. book.proto

python test.py
>>
book: "The Great Gatsby"
author: "F. Scott Fitzgerald"
b'\n\x10The Great Gatsby\x12\x13F. Scott Fitzgerald'
book: "The Great Gatsby"
author: "F. Scott Fitzgerald"
```









