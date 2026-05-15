from spendsentry.alerter import send_alert


def test_send_alert(monkeypatch, mocker):
    # Mock config
    monkeypatch.setattr(
        "spendsentry.alerter.get_config",
        lambda: {
            "alerts": {
                "channel": "telegram",
                "telegram_token": "mock_token",
                "telegram_chat_id": "mock_id",
            }
        },
    )

    mock_post = mocker.patch("httpx.post")
    send_alert("Test Alert")

    mock_post.assert_called_once_with(
        "https://api.telegram.org/botmock_token/sendMessage",
        json={"chat_id": "mock_id", "text": "Test Alert"},
    )
