

def test_home_page(client):
    """
    GIVEN a Flask + RESTX (Swagger) application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """

    # Using the test client configured for testing
    response = client.get('/')
    assert response.status_code == 200
    assert b"ARAS OSLC API" in response.data
    assert b"swagger.json" in response.data
    assert b"clientId" in response.data
