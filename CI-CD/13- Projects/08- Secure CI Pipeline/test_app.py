from app import sanitize_branch_name
def test_sanitize():
    assert sanitize_branch_name("feature/login api") == "feature-login-api"
