from agentmemory import wipe_category
from agentmemory.events import (
    create_event,
    get_epoch,
    get_events,
    increment_epoch,
    reset_epoch,
    set_epoch,
)


def test_reset_epoch():
    reset_epoch()
    assert get_epoch() == 1
    wipe_category("epoch")


def test_set_epoch():
    set_epoch(5)
    assert get_epoch() == 5
    wipe_category("epoch")


def test_increment_epoch():
    reset_epoch()
    assert increment_epoch() == 2
    assert get_epoch() == 2
    wipe_category("epoch")


def test_create_event():
    reset_epoch()
    create_event("test event", metadata={"test": "test"})
    event = get_events()[0]
    assert event["document"] == "test event"
    assert event["metadata"]["test"] == "test"
    assert int(event["metadata"]["epoch"]) == 1
    wipe_category("events")
    wipe_category("epoch")


def test_get_events():
    wipe_category("events")
    reset_epoch()
    for i in range(5):
        create_event("test event " + str(i + 1))
    assert len(get_events()) == 5
    assert get_events(1)[0]["document"] == "test event 5"
    wipe_category("events")
    wipe_category("epoch")
