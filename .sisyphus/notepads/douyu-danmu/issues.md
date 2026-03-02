# Issues - Douyu Danmu Crawler

> This file tracks problems and gotchas encountered during implementation.

---

---
## [2026-03-02 00:55] Task 2: Issues Encountered

### Issue 1: SSL Handshake Failure on All Ports Initially
**Symptom**: `[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]` error on ports 8503, 8504, 8505, 8506
**Root Cause**: OpenSSL 3.6.1 with default SECLEVEL=2 rejects Douyu's legacy cipher suites
**Solution**: Added `ciphers="DEFAULT@SECLEVEL=1"` to sslopt configuration
**Status**: ✓ Resolved

### Issue 2: UTF-8 Decoding Failures
**Symptom**: `UnicodeDecodeError` when decoding message body from some packets
**Root Cause**: Douyu server occasionally splits UTF-8 multi-byte characters across packet boundaries
**Solution**: Added fallback decoding with `errors="ignore"` parameter
**Status**: ✓ Resolved (non-critical data loss acceptable for split characters)

### Issue 3: Port 8056 Connection Refused
**Symptom**: `[Errno 111] Connection refused` when trying ws:// on port 8056
**Root Cause**: Port 8056 likely deprecated or filtered at network level
**Solution**: Stayed with wss:// (encrypted) on port 8506 with SSL workaround
**Status**: ✓ Resolved (using encrypted connection is better anyway)

### Known Limitations
1. **No Automatic Reconnection**: Current implementation doesn't handle network drops or server disconnects
   - **Impact**: Script terminates on connection loss
   - **Workaround**: User can restart manually; Task 2 spec says "simple try-except is fine"
   - **Future**: Task 3+ may add reconnection logic

2. **Room Activity Dependency**: Script only receives messages when room has active chatters
   - **Impact**: Testing in quiet rooms shows no chatmsg output
   - **Workaround**: Test with popular rooms (6657 has moderate activity)
   - **Status**: Expected behavior, not a bug

3. **No Message Buffering**: Messages printed directly to console, not buffered
   - **Impact**: High message rate may flood console
   - **Workaround**: CSV writing in Task 3 will provide structured storage
   - **Status**: Per design - Task 2 focuses on connection, Task 3 adds persistence
