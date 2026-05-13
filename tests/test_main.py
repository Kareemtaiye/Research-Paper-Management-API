from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_health():
    response = client.get("/health")

    assert response.status_code == 200


# def test_foo_not_implemented():
#     def foo():
#         raise NotImplementedError

#     with pytest.raises(RuntimeError) as excinfo:
#         foo()
#     assert excinfo.type is RuntimeError
