from app import deployment_message
def test_message():
    assert deployment_message("staging") == "deployed to staging"
