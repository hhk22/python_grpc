# Async gRPC Chat Example

이 예제는 `grpc.aio` 기반의 비동기 서버와 클라이언트로 간단한 그룹 채팅을 구현합니다. 각 클라이언트는 스트림 RPC 하나를 통해 서버와 양방향으로 메시지를 주고받고, 서버는 모든 참가자에게 메시지를 브로드캐스트합니다.

## 구성 요소

- `chat.proto` / `chat_pb2.py` / `chat_pb2_grpc.py` : 채팅 서비스, 클라이언트 이벤트, 브로드캐스트 메시지를 정의합니다. `ClientEvent` 는 `join`, `message`, `leave` 세 가지 이벤트를 `oneof` 로 구분합니다.
- `server.py` : `grpc.aio.server()` 를 사용한 asyncio 기반 서버입니다. 클라이언트 연결을 `ChatRoom` 으로 관리하고, `ChatService.Chat` RPC 에서 각 클라이언트의 메시지를 받아 모든 참가자에게 전달합니다. 입장/퇴장 시에는 시스템 메시지를 생성해 공지합니다.
- `client.py` : CLI 채팅 클라이언트입니다. 사용자 입력을 비동기로 읽어 서버로 전송하고, 서버에서 받은 메시지를 실시간으로 출력합니다.

## 준비

프로토콜 버퍼 정의를 변경한 경우 다음 명령으로 파이썬 코드를 다시 생성하세요.

```bash
python -m grpc_tools.protoc -I chat --python_out=chat --grpc_python_out=chat chat/chat.proto
```

## 실행 방법

### 1. 서버 실행

```bash
python chat/server.py
```

서버는 기본적으로 `0.0.0.0:50051` (또는 IPv6 `[::]:50051`) 에서 대기하며, 로그로 참가자 입출입을 확인할 수 있습니다.

### 2. 클라이언트 실행

별도 터미널에서 다음 명령을 실행합니다. `--username` 으로 표시 이름을 지정할 수 있습니다.

```bash
python chat/client.py --username alice
```

메시지를 입력하면 서버를 통해 모든 참가자에게 전달됩니다. `Ctrl+D`(Unix) 또는 `Ctrl+Z` 후 Enter(Windows) 를 눌러 종료할 수 있습니다.

## 동작 요약

1. 클라이언트는 스트림을 열며 `JoinRequest` 를 전송하고, 서버는 내부적으로 큐를 만들어 참가자를 등록합니다.
2. 참가자가 전송한 `ChatInput` 은 서버의 `ChatRoom` 이 보관 중인 다른 모든 연결 큐로 브로드캐스트됩니다.
3. 스트림이 종료되거나 클라이언트가 `LeaveRequest` 를 보낼 경우 참가자를 제거하고 퇴장 시스템 메시지를 전파합니다.

## 추가 아이디어

- TLS 인증서를 적용하려면 `grpc.aio.secure_channel` / `grpc.ssl_server_credentials` 로 교체하고, 기존 TLS 예제에서 발급한 인증서를 재사용하세요.
- 메시지 기록 저장, 사용자 인증, 채팅방 분리, WebSocket 게이트웨이 등으로 확장해 볼 수 있습니다.

