from spendsentry.alerter import format_alert_message


def test_format_alert_message():
    commit = {"hash": "abc1234", "message": "feat: add image processor"}
    msg = format_alert_message(2.5, 1.0, commit, "Roll back abc1234")

    assert "$2.50/hr" in msg
    assert "$1.00/hr" in msg
    assert "abc1234" in msg
    assert "feat: add image processor" in msg
    assert "Roll back abc1234" in msg


def test_format_alert_message_no_limit():
    msg = format_alert_message(2.5, None, None, None)

    assert "$2.50/hr" in msg
    assert "Limit:" not in msg
    assert "Probable Cause:" not in msg
