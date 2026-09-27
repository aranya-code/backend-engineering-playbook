from app import health

def test_health():
    assert health() == 'ok'
