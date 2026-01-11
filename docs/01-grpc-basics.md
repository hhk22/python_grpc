# 공부한 내용 1: gRPC 기본기

gRPC는 HTTP/2 위에서 동작하면서 Protocol Buffers를 메시지 포맷으로 사용하는 고성능 RPC 프레임워크다. 텍스트 기반의 REST와 달리 바이너리 직렬화를 활용해 속도·효율을 확보하고, 서비스와 메시지 정의를 기반으로 여러 언어의 서버·클라이언트 코드를 자동 생성할 수 있다.

## 핵심 정리
- **전송 계층**: 기본적으로 HTTP/2를 사용해 다중 스트림, 헤더 압축, 서버 푸시 등을 활용한다.
- **프로토콜 버퍼**: `.proto` 파일 한 장으로 메시지 스키마와 RPC 서비스를 정의하고, 각 언어별 스텁을 생성한다.
- **생산성 향상**: 스키마에서 코드가 생성되므로 언어별 수동 구현 대비 오탈자를 줄이고 유지보수가 쉽다.

## 기본 워크플로우
```bash
conda create --name grpc-python python=3.12
conda activate grpc-python
pip install grpcio grpcio-tools

python -m grpc_tools.protoc \
  -I . \
  --python_out=. \
  --grpc_python_out=. \
  book.proto
```

위 명령으로 `book.proto`에 정의한 메시지를 직렬화/역직렬화할 수 있는 코드와 gRPC 서비스 스텁을 생성한다. 생성된 모듈을 활용하면 다음과 같이 직렬화한 뒤 다시 복원해 검증할 수 있다.

```python
import book_pb2

book = book_pb2.Book(book="The Great Gatsby", author="F. Scott Fitzgerald")
serialized = book.SerializeToString()
restored = book_pb2.Book()
restored.ParseFromString(serialized)
```

## 기억할 만한 포인트
- proto3 문법은 기본값과 옵셔널 처리 규칙이 간단해 입문자가 접근하기 좋다.
- 바이너리 포맷이기 때문에 네트워크 대역폭과 파싱 비용이 작아 모바일·IoT 환경에서도 효율적이다.
- 서비스 정의를 통해 RPC 시그니처를 표준화하면 팀 간 계약(Contract) 관리가 쉬워진다.

## 코드 전체 전문

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


