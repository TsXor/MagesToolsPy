from typing import Iterable

class SCXCodec:
    charset: dict[int, int]
    _revmap: dict[int, int]

    def __init__(self, charset: dict[int, int]) -> None:
        self.charset = charset
        self._revmap = {v: k for k, v in charset.items()}

    @classmethod
    def from_string(cls, charset: str, omit_char: str = '\0'):
        return cls({i: ord(c) for i, c in enumerate(charset) if c != omit_char})
    
    @classmethod
    def base_on(cls, base: 'SCXCodec', replaces: Iterable[tuple[str, str]]):
        new_charset = base.charset.copy()
        for orig, new in replaces:
            new_charset[base._revmap[ord(orig)]] = ord(new)
        return cls(new_charset)

    def decode(self, data: Iterable[int]):
        return ''.join(chr(self.charset[c]) for c in data)

    def encode(self, data: str):
        for c in data: yield self._revmap[ord(c)]

DEFAULT_CODEC = SCXCodec.from_string(
    ' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz\u3000' \
    "/:-;!?'.@#%~*&`()°^>+<ﾉ･=″$′,[\\]_{|}\ue000\ue001\ue002\ue003\ue004\ue005\ue006\ue007\ue008\ue009\ue00a\ue00b\ue00c\ue00d\ue00e\ue00f\ue010\ue011\ue012\ue013\ue014\ue015\ue016\ue017\ue018\ue019\ue01a…" \
    '０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ、。' \
    '，．：；？！゛゜‘’“”（）〔〕［］｛｝〈〉《》「」『』【】＜＞〖〗・⋯〜ー♪―ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ①②' \
    '③④⑤⑥⑦⑧⑨⑩⑪⑫⑬ⁿ\ue01c²\ue01d\ue01e\ue01f\ue020％–—＿／•\ue021\ue022\ue023\ue024\ue025\ue026\ue027\ue028\ue029\ue02a\ue02b\ue02c\ue02d\ue02e\ue02f\ue030\ue031\ue032\ue033\ue034\ue035\ue036\ue037\ue038\ue039\ue03a\ue03b\ue03c\ue03d\ue03e\ue03f\ue040\ue041\ue042\ue043\ue044\ue045\ue046\ue047\ue048' \
    '\ue049\ue04a\ue04b\ue04c\ue04d\ue04e\ue04f\ue050\ue051\ue052\ue053\ue054\ue055\ue056\ue057\ue058\ue059\ue05a\ue05b\ue05c\ue05d\ue05e\ue05f\ue060\ue061\ue062\ue063\ue064\ue065\ue066\ue067βγζημξρστυφχψωÅ√◯⌐¬\ue068∣¯Д∥αδεθικλνο' \
    'πヽヾゝゞ〃仝々〆〇＼＋－±×÷＝≠＜＞≦≧∞∴♂♀℃￥＄￠￡％＃＆＊＠§☆★○●◎◇◆□■△▲▽▼※〒→←↑↓〓∈∋⊆⊇⊂⊃∪' \
    '∩∧∨￢⇒⇔∀∃∠⊥⌒∂∇≡≒≪≫∽∝∵∫∬‰♯♭♪†‡¶あいうえおかがきぎくぐけげこごさざしじすずせぜそぞただちぢつづてでとど' \
    'なにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもやゆよらりるれろわゐゑをんアイウエオカガキギクグケゲコゴサザシジスズ セゼソゾタ' \
    'ダチヂツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモヤユヨラリルレロヮワヰヱヲンヴΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟ' \
    'ΠΡΣΤΥΦΧΨΩⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ∮∑∟⊿Я'
)
