from abc import ABC, abstractmethod
from io import BytesIO
from array import array
from typing import ByteString, Iterable, Callable
from enum import IntEnum
from .codec import DEFAULT_CODEC
from mages_tools.errors import *
from mages_tools.io import *


class TokenType(IntEnum):
    LineBreak               = 0b00000000
    CharacterName           = 0b00000001
    DialogueLine            = 0b00000010
    Present                 = 0b00000011
    SetColor                = 0b00000100
    PresentResetAlignment   = 0b00001000
    RubyBase                = 0b00001001
    RubyTextStart           = 0b00001010
    RubyTextEnd             = 0b00001011
    SetFontSize             = 0b00001100
    ChaosCommand1           = 0b00001110 # WTFToken
    SetAlignmentCenter      = 0b00001111
    SetTopMargin            = 0b00010001
    SetLeftMargin           = 0b00010010
    EvaluateExpression      = 0b00010101
    ChaosCommand2           = 0b00011000 # WTFToken2
    ChaosCommand3           = 0b00011001 # WTFShort
    TextBit                 = 0b10000000
    Termination             = 0b11111111

class SCXToken(ABC):
    type: TokenType

    def __init__(self, typ: TokenType):
        self.type = typ

    @classmethod
    @abstractmethod
    def load(cls, typ: TokenType, data: Readable) -> 'SCXToken': pass

    @abstractmethod
    def dump(self, data: Writable): pass

registry = dict[TokenType, type[SCXToken]]()

def register_for(code: TokenType):
    def register(typ: type[SCXToken]):
        if code in registry:
            raise ValueError(f'type {code} already assigned to {registry[code]}')
        registry[code] = typ
        return typ
    return register

@register_for(TokenType.LineBreak)
@register_for(TokenType.CharacterName)
@register_for(TokenType.DialogueLine)
@register_for(TokenType.Present)
@register_for(TokenType.PresentResetAlignment)
@register_for(TokenType.RubyBase)
@register_for(TokenType.RubyTextStart)
@register_for(TokenType.RubyTextEnd)
@register_for(TokenType.ChaosCommand1)
@register_for(TokenType.ChaosCommand2)
@register_for(TokenType.SetAlignmentCenter)
class BareToken(SCXToken):
    @classmethod
    def load(cls, typ: TokenType, data: Readable):
        return cls(typ)

    def dump(self, data: Writable):
        data.write_u8(self.type.value)

    def __repr__(self):
        return f'<{self.type.name}()>'

@register_for(TokenType.SetFontSize)
@register_for(TokenType.SetTopMargin)
@register_for(TokenType.SetLeftMargin)
@register_for(TokenType.ChaosCommand3)
class UnaryToken(SCXToken):
    arg: int

    def __init__(self, typ: TokenType, arg: int):
        super().__init__(typ)
        self.arg = arg

    @classmethod
    def load(cls, typ: TokenType, data: Readable):
        return cls(typ, data.read_i16())

    def dump(self, data: Writable):
        data.write_u8(self.type.value)
        data.write_i16(self.arg)

    def __repr__(self):
        return f'<{self.type.name}({self.arg})>'

@register_for(TokenType.SetColor)
@register_for(TokenType.EvaluateExpression)
class ExpressionToken(SCXToken):
    args: list[tuple[int, bytes]]

    def __init__(self, typ: TokenType, args: list[tuple[int, bytes]]):
        super().__init__(typ)
        self.args = args

    @classmethod
    def load(cls, typ: TokenType, data: Readable):
        args = list[tuple[int, bytes]]()
        while (ctrl := data.read_u8()) != 0:
            arglen = (ctrl & 0b01100000) >> 5
            args.append((ctrl, data.read(arglen)))
        return cls(typ, args)

    def dump(self, data: Writable):
        data.write_u8(self.type.value)
        for ctrl, expr in self.args:
            data.write_u8(ctrl)
            data.write(expr)
        data.write_u8(0)

    def __repr__(self):
        return f'<{self.type.name}({self.args})>'


def tokenize(data: Readable, decoder: Callable[['array[int]'], str] = DEFAULT_CODEC.decode):
    text_buf = array('H')
    while (code := data.read_u8()) != TokenType.Termination:
        if code & TokenType.TextBit:
            hi = code & ~TokenType.TextBit
            lo = data.read_u8()
            text_buf.append((hi << 8) | lo)
        else:
            if text_buf:
                text = decoder(text_buf)
                text_buf = array('H') # array不能clear，这是workaround
                yield text
            try: typ = TokenType(code)
            except ValueError: raise ValueError(f'unknown token type {bin(code)}')
            yield registry[typ].load(typ, data)
    if text_buf:
        yield decoder(text_buf)

def tokenize_from_buffer(strn: ByteString, decoder: Callable[['array[int]'], str] = DEFAULT_CODEC.decode):
    yield from tokenize(ROBuffer(strn), decoder)

def untokenize(tokens: Iterable[str | SCXToken], data: Writable, encoder: Callable[[str], Iterable[int]] = DEFAULT_CODEC.encode):
    for token in tokens:
        if isinstance(token, SCXToken):
            token.dump(data)
        elif isinstance(token, str):
            for u16ord in encoder(token):
                hi = u16ord >> 8
                lo = u16ord & 0xFF
                data.write_u8(hi | TokenType.TextBit)
                data.write_u8(lo)
        else:
            raise ValueError('invalid token')

def untokenize_to_buffer(tokens: Iterable[str | SCXToken], encoder: Callable[[str], Iterable[int]] = DEFAULT_CODEC.encode):
    buf = BytesIO()
    untokenize(tokens, FileWrapper(buf), encoder)
    return buf.getvalue()
