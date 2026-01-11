# 미니 프로젝트: 실시간 gRPC 채팅

학습 내용을 토대로 양방향 스트리밍을 활용한 간단한 채팅 서비스를 구현했다. `chatting_project/` 디렉터리에 서버·클라이언트 코드와 `.proto` 정의가 포함되어 있다.

## 목표
- gRPC bidirectional streaming 패턴에 익숙해지기.
- asyncio 기반 서버에서 여러 클라이언트를 동시에 처리하기.
- 컨텍스트·메타데이터·큐 등을 활용해 안정적인 스트림 종료 로직을 구성하기.

## 구성 요소
- **ChatRoom**: 연결된 클라이언트별 비동기 큐를 관리하고, 시스템 메시지와 사용자 메시지를 브로드캐스트한다.
- **ChatService**: `Chat(stream ClientEvent) returns (stream ChatMessage)` 메서드를 구현해 Join/Message/Leave 이벤트를 처리한다.
- **Async Client**: 표준 입력을 `asyncio.to_thread`로 비동기 처리해 메시지를 전송하고, 서버의 스트림을 실시간으로 출력한다.

## 주요 구현 포인트
- **접속 관리**: 각 클라이언트는 `context.peer()`와 UUID 조합으로 고유 ID를 부여받고, `asyncio.Queue`에 메시지를 저장한다.
- **시스템 메시지**: 입장/퇴장 시 `[system]` 프리픽스를 가진 공지 메시지를 자동으로 브로드캐스트한다.
- **우아한 종료**: 서버가 연결을 정리할 때 비어 있는 시스템 메시지를 큐에 넣어 제너레이터 루프를 깨우고, 클라이언트는 `KeyboardInterrupt`와 `asyncio.CancelledError`를 처리해 종료한다.
- **이중 스트리밍**: 클라이언트는 `yield`로 이벤트를 보낸 뒤 `async for`로 응답 스트림을 소비하며, 서버는 소비·생산을 별도 태스크로 나눠 백프레셔를 제어한다.

## 실행 방법
```bash
python chatting_project/server.py
# 새 터미널
python chatting_project/client.py --username hyeonghwan
python chatting_project/client.py --username guest
```

## 배운 점
- 비동기 큐와 태스크를 조합하면 별도 프레임워크 없이도 실시간 서비스를 구축할 수 있다.
- 스트림 종료 시점을 명확히 정의하고 센티넬 메시지를 사용하는 것이 중요하다.
- gRPC의 추상화 덕분에 네트워크 세부사항보다 비즈니스 로직과 동시성 제어에 집중할 수 있었다.

