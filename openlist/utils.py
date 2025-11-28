"""
OpenList 工具函数模块。

提供时间转换和签名生成等实用工具函数。
"""

import hmac
import hashlib
import base64
from datetime import datetime, timezone, date
import numbers
from typing import Union, TypeAlias
from numbers import Real


TimeLike: TypeAlias = Union[datetime, date, str, Real]
"""时间类型别名，支持 datetime、date、ISO 格式字符串或数值时间戳。"""


def to_utc_timestamp(t: TimeLike) -> int:
    """将多种时间表示形式转换为 UTC Unix 时间戳。

    支持以下输入类型：
    - 数值类型（int/float）：直接作为时间戳返回
    - ISO 8601 格式字符串：解析后转换
    - datetime 对象：转换为 UTC 时间戳
    - date 对象：转换为当天 00:00:00 UTC 的时间戳

    Args:
        t: 时间表示，可以是 datetime、date、ISO 格式字符串或数值时间戳。

    Returns:
        UTC Unix 时间戳（秒，整数）。

    Raises:
        ValueError: 当字符串格式无法解析为有效时间时抛出。
        TypeError: 当输入类型不受支持时抛出。

    Examples:
        >>> to_utc_timestamp(1700000000)
        1700000000
        >>> to_utc_timestamp("2023-11-14T22:13:20+00:00")
        1700000000
        >>> from datetime import datetime, timezone
        >>> to_utc_timestamp(datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc))
        1700000000
    """
    if isinstance(t, numbers.Real):
        return int(t)

    if isinstance(t, str):
        try:
            t = datetime.fromisoformat(t)
        except ValueError:
            raise ValueError(f"无法解析的时间字符串格式: {t}")
    if isinstance(t, datetime):
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        else:
            t = t.astimezone(timezone.utc)
        return int(t.timestamp())
    if isinstance(t, date):
        dt = datetime(t.year, t.month, t.day, tzinfo=timezone.utc)
        return int(dt.timestamp())
    raise TypeError(f"不支持的时间表示类型: {type(t)}")


def sign(path: str, token: str, expire: TimeLike = 0) -> str:
    """生成 OpenList 资源访问签名。

    使用 HMAC-SHA256 算法生成 URL 安全的 Base64 编码签名。
    原算法（NodeJS）：https://doc.oplist.org/guide/drivers/common#_3-developing-on-your-own
    签名使用原始路径而非 URL 编码路径。

    Args:
        path: 需要签名的资源路径，如 "/path/to/file.txt"。
        token: 签名令牌，可在 OpenList 后台「设置 → 其他 → 令牌」获取。
        expire: 签名过期时间，支持多种格式（参见 :data:`TimeLike`）。
            默认为 0，即永不过期。

    Returns:
        格式为 "{base64_signature}:{expire_timestamp}" 的签名字符串。
    """
    expire_timestamp: int = to_utc_timestamp(expire)
    to_sign: str = f"{path}:{expire_timestamp}"
    to_sign_bytes = to_sign.encode('utf-8')
    token_bytes = token.encode('utf-8')
    hmac_digest = hmac.new(
        key=token_bytes,
        msg=to_sign_bytes,
        digestmod=hashlib.sha256
    ).digest()
    base64_sign_bytes = base64.urlsafe_b64encode(hmac_digest).rstrip(b'=')
    _sign = base64_sign_bytes.decode('utf-8')
    sign = f"{_sign}:{expire_timestamp}"
    return sign

