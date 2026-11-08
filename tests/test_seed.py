from app.seed import seed_demo_data


def test_seed_demo_hides_passwords_on_render(app, monkeypatch):
    monkeypatch.setenv("RENDER", "true")

    message = seed_demo_data()

    assert "Demo data created." in message
    assert "admin1234" not in message
    assert "provider1234" not in message
