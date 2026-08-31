import pytest
import sqlite3
import datetime
from unittest.mock import MagicMock
from topic_watcher.agent import AlertAgent, AlertGroup


def test_get_topic_name_all():
    # String topic
    assert AlertGroup.get_topic_name("some/topic") == "some/topic"
    
    # /all topic
    res = AlertGroup.get_topic_name(("devices/fakedevice/all", "temperature"))
    assert res == "devices/fakedevice/temperature"


def test_get_topic_name_multi():
    # /multi topic (added in PR #11)
    res = AlertGroup.get_topic_name(("devices/fakedevice/multi", "temperature"))
    assert res == "devices/fakedevice/temperature"

    res2 = AlertGroup.get_topic_name(("campus/building/unit/multi", "power"))
    assert res2 == "campus/building/unit/power"


def test_get_topic_name_invalid():
    with pytest.raises(ValueError) as excinfo:
        AlertGroup.get_topic_name(("devices/fakedevice/custom", "point"))
    assert "Invalid topic and point name" in str(excinfo.value)
    assert "/all or /multi" in str(excinfo.value)


def test_alert_group_config_parsing():
    mock_agent = MagicMock()
    conn = sqlite3.connect(":memory:")
    
    config = {
        "heartbeat/topic": 10,
        "devices/campus/building/device1/all": {
            "seconds": 5,
            "points": ["temp", "pressure"]
        },
        "devices/campus/building/device2/multi": {
            "seconds": 8,
            "points": ["status", "load"]
        }
    }
    
    group = AlertGroup(
        group_name="test_group",
        config=config,
        connection=conn,
        main_agent=mock_agent,
        publish_local=True,
        publish_remote=False
    )
    
    assert group.wait_time["heartbeat/topic"] == 10
    assert group.wait_time["devices/campus/building/device1/all"] == 5
    assert group.wait_time["devices/campus/building/device2/multi"] == 8
    
    assert "temp" in group.point_ttl["devices/campus/building/device1/all"]
    assert "pressure" in group.point_ttl["devices/campus/building/device1/all"]
    assert "status" in group.point_ttl["devices/campus/building/device2/multi"]
    assert "load" in group.point_ttl["devices/campus/building/device2/multi"]
