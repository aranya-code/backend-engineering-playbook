from app import runtime_message

def test_runtime_message():
    assert "Python" in runtime_message()
