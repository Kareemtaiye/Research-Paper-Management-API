# from conftest import client:  pytest automatically inject fixtures, so i domt need this


def test_auth_flow(client):
    data = {"username": "test_user", "password": "test_password"}

    register_res = client.post("/auth/register", data=data)

    assert register_res.status_code == 201

    # login_res = client.post("/auth/login", data=data)
    # assert login_res.status_code == 201


# def test_login(client):
#     request_data = {"username": "test", "password": "data"}
#     response = client.post("/auth/token", data=request_data)

#     assert response.status_code == 200
