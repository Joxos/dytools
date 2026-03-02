# Learnings - Douyu Danmu Crawler

> This file tracks conventions, patterns, and best practices discovered during implementation.

---

---
## [2026-03-02 00:55] Task 2: Binary Protocol & SSL Patterns

### Binary Protocol Patterns
1. **Little-Endian Packing**: Always use `struct.pack('<I', value)` for Douyu protocol integers
2. **Message Type Constants**: CLIENT_MSG_TYPE=689 (client→server), SERVER_MSG_TYPE=690 (server→client)
3. **Packet Structure**: Length field appears TWICE in header (offset 0 and offset 4)
4. **Body Calculation**: `packet_length = len(body) + 8` (excludes first 4 bytes)
5. **Null Terminator**: Message body MUST end with `\0` byte

### WebSocket-Client Library Usage
1. **Binary Messages**: Use `ws.send(data, opcode=0x2)` for binary frames
2. **SSL Options**: Pass `sslopt` dict to `run_forever()` method, not to WebSocketApp constructor
3. **Callbacks**: All callbacks receive `ws` as first parameter (on_open, on_message, on_error, on_close)
4. **Threading**: Heartbeat logic runs in separate daemon thread to avoid blocking message reception

### SSL/TLS Compatibility
1. **OpenSSL 3.x Issue**: Default SECLEVEL=2 rejects older ciphers used by many Chinese services
2. **Workaround**: Set `ciphers="DEFAULT@SECLEVEL=1"` in sslopt to enable backward compatibility
3. **TLS Version**: Use `ssl.PROTOCOL_TLS_CLIENT` instead of hardcoded TLS 1.2 for better negotiation
4. **Certificate Validation**: Douyu requires `cert_reqs=ssl.CERT_NONE` and `check_hostname=False`

### Message Parsing Gotchas
1. **Escape Sequences**: MUST unescape @A→@ and @S→/ BEFORE splitting by `/`
2. **Unescaping Order**: Replace @S first, then @A (or use proper state machine to avoid double replacement)
   - **CORRECTION**: Actually replace in reverse - @S then @A works because @ appears in @A
3. **Split Behavior**: `str.split('/')` leaves empty string if trailing `/` exists - use `rstrip('/')` first
4. **UTF-8 Boundaries**: Server may split multi-byte UTF-8 characters across packets - handle UnicodeDecodeError gracefully

### Threading Best Practices
1. **Daemon Threads**: Heartbeat thread marked as `daemon=True` so it auto-terminates with main thread
2. **Running Flag**: Use `self.running` boolean to coordinate shutdown between threads
3. **Sleep Interval**: `time.sleep(45)` for heartbeat matches Douyu spec exactly
4. **Thread Safety**: WebSocket-client handles thread safety internally for send operations

### Debugging Tips
1. **Verbose Mode**: Use `--verbose` flag to see all DEBUG logs including raw message strings
2. **Message Inspection**: Log serialized messages before encoding to verify format
3. **Connection Test**: Successful loginres is the key indicator of proper protocol implementation
4. **Port Testing**: Try multiple ports (8501-8506) if initial connection fails
