import re
import sys
import traceback

import pytest

from .._util import *


def test_ProtocolError():
    with pytest.raises(TypeError):
        ProtocolError("abstract base class")


def test_LocalProtocolError():
    try:
        raise LocalProtocolError("foo")
    except LocalProtocolError as e:
        assert str(e) == "foo"
        assert e.error_status_hint == 400

    try:
        raise LocalProtocolError("foo", error_status_hint=418)
    except LocalProtocolError as e:
        assert str(e) == "foo"
        assert e.error_status_hint == 418

    def thunk():
        raise LocalProtocolError("a", error_status_hint=420)

    try:
        try:
            thunk()
        except LocalProtocolError as exc1:
            orig_traceback = "".join(traceback.format_tb(sys.exc_info()[2]))
            exc1._reraise_as_remote_protocol_error()
    except RemoteProtocolError as exc2:
        assert type(exc2) is RemoteProtocolError
        assert exc2.args == ("a",)
        assert exc2.error_status_hint == 420
        new_traceback = "".join(traceback.format_tb(sys.exc_info()[2]))
        assert new_traceback.endswith(orig_traceback)


def test_validate():
    my_re = re.compile(br"(?P<group1>[0-9]+)\.(?P<group2>[0-9]+)")
    with pytest.raises(LocalProtocolError):
        validate(my_re, b"0.")

    groups = validate(my_re, b"0.1")
    assert groups == {"group1": b"0", "group2": b"1"}

    # successful partial matches are an error - must match whole string
    with pytest.raises(LocalProtocolError):
        validate(my_re, b"0.1xx")
    with pytest.raises(LocalProtocolError):
        validate(my_re, b"0.1\n")


def test_validate_formatting():
    my_re = re.compile(br"foo")

    with pytest.raises(LocalProtocolError) as excinfo:
        validate(my_re, b"", "oops")
    assert "oops" in str(excinfo.value)

    with pytest.raises(LocalProtocolError) as excinfo:
        validate(my_re, b"", "oops {}")
    assert "oops {}" in str(excinfo.value)

    with pytest.raises(LocalProtocolError) as excinfo:
        validate(my_re, b"", "oops {} xx", 10)
    assert "oops 10 xx" in str(excinfo.value)


def test_make_sentinel():
    S = make_sentinel("S")
    assert repr(S) == "S"
    assert S == S
    assert type(S).__name__ == "S"
    assert S in {S}
    assert type(S) is S
    S2 = make_sentinel("S2")
    assert repr(S2) == "S2"
    assert S != S2
    assert S not in {S2}
    assert type(S) is not type(S2)


def test_bytesify():
    assert bytesify(b"123") == b"123"
    assert bytesify(bytearray(b"123")) == b"123"
    assert bytesify("123") == b"123"

    with pytest.raises(UnicodeEncodeError):
        bytesify(u"\u1234")

    with pytest.raises(TypeError):
        bytesify(10)
