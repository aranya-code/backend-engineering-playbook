from app import greeting
def test_greeting():
    assert greeting("GitHub Actions") == "Hello, GitHub Actions!"
