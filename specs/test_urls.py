
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

import isso

client = Client(isso.Isso(123), BaseResponse)


def test_200ok():

    assert client.get('/').status_code == 200
    assert client.get('/comment/asdf/123').status_code == 200
