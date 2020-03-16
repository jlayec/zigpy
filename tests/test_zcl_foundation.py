import zigpy.types as t
from zigpy.zcl import foundation


def test_typevalue():
    tv = foundation.TypeValue()
    tv.type = 0x20
    tv.value = t.uint8_t(99)
    ser = tv.serialize()
    r = repr(tv)
    assert r.startswith("<") and r.endswith(">")
    assert "type=uint8_t" in r
    assert "value=99" in r

    tv2, data = foundation.TypeValue.deserialize(ser)
    assert data == b""
    assert tv2.type == tv.type
    assert tv2.value == tv.value


def test_read_attribute_record():
    orig = b"\x00\x00\x00\x20\x99"
    rar, data = foundation.ReadAttributeRecord.deserialize(orig)
    assert data == b""
    assert rar.status == 0
    assert isinstance(rar.value, foundation.TypeValue)
    assert isinstance(rar.value.value, t.uint8_t)
    assert rar.value.value == 0x99

    r = repr(rar)
    assert len(r) > 5
    assert r.startswith("<") and r.endswith(">")

    ser = rar.serialize()
    assert ser == orig


def test_attribute_reporting_config_0():
    arc = foundation.AttributeReportingConfig()
    arc.direction = 0
    arc.attrid = 99
    arc.datatype = 0x20
    arc.min_interval = 10
    arc.max_interval = 20
    arc.reportable_change = 30
    ser = arc.serialize()

    arc2, data = foundation.AttributeReportingConfig.deserialize(ser)
    assert data == b""
    assert arc2.direction == arc.direction
    assert arc2.attrid == arc.attrid
    assert arc2.datatype == arc.datatype
    assert arc2.min_interval == arc.min_interval
    assert arc2.max_interval == arc.max_interval
    assert arc.reportable_change == arc.reportable_change


def test_attribute_reporting_config_1():
    arc = foundation.AttributeReportingConfig()
    arc.direction = 1
    arc.attrid = 99
    arc.timeout = 0x7E
    ser = arc.serialize()

    arc2, data = foundation.AttributeReportingConfig.deserialize(ser)
    assert data == b""
    assert arc2.direction == arc.direction
    assert arc2.timeout == arc.timeout


def test_typed_collection():
    tc = foundation.TypedCollection()
    tc.type = 0x20
    tc.value = t.LVList(t.uint8_t)([t.uint8_t(i) for i in range(100)])
    ser = tc.serialize()

    assert len(ser) == 1 + 1 + 100  # type, length, values

    tc2, data = foundation.TypedCollection.deserialize(ser)

    assert tc2.type == 0x20
    assert tc2.value == list(range(100))


def test_write_attribute_status_record():
    attr_id = b"\x01\x00"
    extra = b"12da-"
    res, d = foundation.WriteAttributesStatusRecord.deserialize(
        b"\x00" + attr_id + extra
    )
    assert res.status == foundation.Status.SUCCESS
    assert res.attrid is None
    assert d == attr_id + extra
    r = repr(res)
    assert r.startswith("<" + foundation.WriteAttributesStatusRecord.__name__)
    assert "status" in r
    assert "attrid" not in r

    res, d = foundation.WriteAttributesStatusRecord.deserialize(
        b"\x87" + attr_id + extra
    )
    assert res.status == foundation.Status.INVALID_VALUE
    assert res.attrid == 0x0001
    assert d == extra

    r = repr(res)
    assert "status" in r
    assert "attrid" in r

    rec = foundation.WriteAttributesStatusRecord(foundation.Status.SUCCESS, 0xAABB)
    assert rec.serialize() == b"\x00"
    rec.status = foundation.Status.UNSUPPORTED_ATTRIBUTE
    assert rec.serialize()[0:1] == foundation.Status.UNSUPPORTED_ATTRIBUTE.serialize()
    assert rec.serialize()[1:] == b"\xbb\xaa"


def test_configure_reporting_response_serialization():
    direction_attr_id = b"\x00\x01\x10"
    extra = b"12da-"
    res, d = foundation.ConfigureReportingResponseRecord.deserialize(
        b"\x00" + direction_attr_id + extra
    )
    assert res.status == foundation.Status.SUCCESS
    assert res.direction is None
    assert res.attrid is None
    assert d == direction_attr_id + extra
    r = repr(res)
    assert r.startswith("<" + foundation.ConfigureReportingResponseRecord.__name__)
    assert "status" in r
    assert "direction" not in r
    assert "attrid" not in r

    res, d = foundation.ConfigureReportingResponseRecord.deserialize(
        b"\x8c" + direction_attr_id + extra
    )
    assert res.status == foundation.Status.UNREPORTABLE_ATTRIBUTE
    assert res.direction is not None
    assert res.attrid == 0x1001
    assert d == extra

    r = repr(res)
    assert "status" in r
    assert "direction" in r
    assert "attrid" in r

    rec = foundation.ConfigureReportingResponseRecord(
        foundation.Status.SUCCESS, 0x00, 0xAABB
    )
    assert rec.serialize() == b"\x00"
    rec.status = foundation.Status.UNREPORTABLE_ATTRIBUTE
    assert rec.serialize()[0:1] == foundation.Status.UNREPORTABLE_ATTRIBUTE.serialize()
    assert rec.serialize()[1:] == b"\x00\xbb\xaa"


def test_status_undef():
    data = b"\xaa"
    extra = b"extra"

    status, rest = foundation.Status.deserialize(data + extra)
    assert rest == extra
    assert status == 0xAA
    assert status.value == 0xAA
    assert status.name == "undefined_0xaa"
    assert isinstance(status, foundation.Status)


def test_frame_control():
    """Test FrameControl frame_type."""
    extra = b"abcd\xaa\x55"
    frc, rest = foundation.FrameControl.deserialize(b"\x00" + extra)
    assert rest == extra
    assert frc.frame_type == foundation.FrameType.GLOBAL_COMMAND

    frc, rest = foundation.FrameControl.deserialize(b"\x01" + extra)
    assert rest == extra
    assert frc.frame_type == foundation.FrameType.CLUSTER_COMMAND

    frc.frame_type = 0x01
    assert frc.frame_type is foundation.FrameType.CLUSTER_COMMAND

    r = repr(frc)
    assert isinstance(r, str)
    assert r.startswith("<")
    assert r.endswith(">")


def test_frame_control_general():
    frc = foundation.FrameControl.general(is_reply=False)
    assert frc.is_cluster is False
    assert frc.is_general is True
    data = frc.serialize()

    assert data == b"\x00"
    assert frc.is_manufacturer_specific is False
    frc.is_manufacturer_specific = False
    assert frc.serialize() == b"\x00"
    frc.is_manufacturer_specific = True
    assert frc.serialize() == b"\x04"

    frc = foundation.FrameControl.general(is_reply=False)
    assert frc.is_reply is False
    assert frc.serialize() == b"\x00"
    frc.is_reply = False
    assert frc.serialize() == b"\x00"
    frc.is_reply = True
    assert frc.serialize() == b"\x08"
    assert foundation.FrameControl.general(is_reply=True).serialize() == b"\x18"

    frc = foundation.FrameControl.general(is_reply=False)
    assert frc.disable_default_response is False
    assert frc.serialize() == b"\x00"
    frc.disable_default_response = False
    assert frc.serialize() == b"\x00"
    frc.disable_default_response = True
    assert frc.serialize() == b"\x10"


def test_frame_control_cluster():
    frc = foundation.FrameControl.cluster(is_reply=False)
    assert frc.is_cluster is True
    assert frc.is_general is False
    data = frc.serialize()

    assert data == b"\x01"
    assert frc.is_manufacturer_specific is False
    frc.is_manufacturer_specific = False
    assert frc.serialize() == b"\x01"
    frc.is_manufacturer_specific = True
    assert frc.serialize() == b"\x05"

    frc = foundation.FrameControl.cluster(is_reply=False)
    assert frc.is_reply is False
    assert frc.serialize() == b"\x01"
    frc.is_reply = False
    assert frc.serialize() == b"\x01"
    frc.is_reply = True
    assert frc.serialize() == b"\x09"
    assert foundation.FrameControl.cluster(is_reply=True).serialize() == b"\x19"

    frc = foundation.FrameControl.cluster(is_reply=False)
    assert frc.disable_default_response is False
    assert frc.serialize() == b"\x01"
    frc.disable_default_response = False
    assert frc.serialize() == b"\x01"
    frc.disable_default_response = True
    assert frc.serialize() == b"\x11"


def test_frame_header():
    """Test frame header deserialization."""
    data = b"\x1c_\x11\xc0\n"
    extra = b"\xaa\xaa\x55\x55"
    hdr, rest = foundation.ZCLHeader.deserialize(data + extra)

    assert rest == extra
    assert hdr.command_id == 0x0A
    assert hdr.is_reply is True
    assert hdr.manufacturer == 0x115F
    assert hdr.tsn == 0xC0

    assert hdr.serialize() == data

    # check no manufacturer
    hdr.frame_control.is_manufacturer_specific = False
    assert hdr.serialize() == b"\x18\xc0\n"

    r = repr(hdr)
    assert isinstance(r, str)
    assert r.startswith("<")
    assert r.endswith(">")


def test_frame_header_general():
    """Test frame header general command."""
    (tsn, cmd_id, manufacturer) = (0x11, 0x15, 0x3344)

    hdr = foundation.ZCLHeader.general(tsn, cmd_id, manufacturer)
    assert hdr.frame_control.frame_type == foundation.FrameType.GLOBAL_COMMAND
    assert hdr.command_id == cmd_id
    assert hdr.tsn == tsn
    assert hdr.manufacturer == manufacturer
    assert hdr.frame_control.is_manufacturer_specific is True

    hdr.manufacturer = None
    assert hdr.manufacturer is None
    assert hdr.frame_control.is_manufacturer_specific is False


def test_frame_header_cluster():
    """Test frame header cluster command."""
    (tsn, cmd_id, manufacturer) = (0x11, 0x16, 0x3344)

    hdr = foundation.ZCLHeader.cluster(tsn, cmd_id, manufacturer)
    assert hdr.frame_control.frame_type == foundation.FrameType.CLUSTER_COMMAND
    assert hdr.command_id == cmd_id
    assert hdr.tsn == tsn
    assert hdr.manufacturer == manufacturer
    assert hdr.frame_control.is_manufacturer_specific is True

    hdr.manufacturer = None
    assert hdr.manufacturer is None
    assert hdr.frame_control.is_manufacturer_specific is False


def test_data_types():
    """Test data types mappings."""
    assert len(foundation.DATA_TYPES) == len(foundation.DATA_TYPE_IDX)
    data_types_set = set([d[1] for d in foundation.DATA_TYPES.values()])
    dt_2_id_set = set(foundation.DATA_TYPE_IDX.keys())
    assert data_types_set == dt_2_id_set


def test_attribute_report():
    a = foundation.AttributeReportingConfig()
    a.direction = 0x01
    a.attrid = 0xAA55
    a.timeout = 900
    b = foundation.AttributeReportingConfig(a)
    assert a.attrid == b.attrid
    assert a.direction == b.direction
    assert a.timeout == b.timeout
