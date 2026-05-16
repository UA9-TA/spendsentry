from spendsentry.config import load_config, save_config


def test_config(tmp_path, monkeypatch):
    monkeypatch.setattr("spendsentry.config.Path.home", lambda: tmp_path)

    cfg = load_config()
    assert cfg == {}

    save_config({"provider": {"name": "aws"}, "limits": {"daily": 50.0}})

    cfg2 = load_config()
    assert cfg2["provider"]["name"] == "aws"
    assert cfg2["limits"]["daily"] == 50.0
