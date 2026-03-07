class _UnsignedIntParser:
    def parse(self, data: bytes) -> int: ...
    def build(self, obj: int) -> bytes: ...

Int8ul: _UnsignedIntParser
Int16ul: _UnsignedIntParser
Int32ul: _UnsignedIntParser
