from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db

URL_NEWS_DETAIL = pytest.lazy_fixture('detail_url')
URL_LOGIN = pytest.lazy_fixture('url_login')
URL_SIGNUP = pytest.lazy_fixture('url_signup')
URL_HOME = pytest.lazy_fixture('home_url')
URL_LOGOUT = pytest.lazy_fixture('url_logout')
AUTHOR_CLIENT = pytest.lazy_fixture('auth_client')
READER_CLIENT = pytest.lazy_fixture('reader_client')
URL_COMMENT_EDIT = pytest.lazy_fixture('url_comment_edit')
URL_COMMENT_DELETE = pytest.lazy_fixture('url_comment_delete')
ANONYMOUS_CLIENT = pytest.lazy_fixture('client')


@pytest.mark.parametrize(
    'url, _client, status',
    (
        (URL_NEWS_DETAIL, ANONYMOUS_CLIENT, HTTPStatus.OK),
        (URL_LOGIN, ANONYMOUS_CLIENT, HTTPStatus.OK),
        (URL_HOME, ANONYMOUS_CLIENT, HTTPStatus.OK),
        (URL_LOGOUT, ANONYMOUS_CLIENT, HTTPStatus.METHOD_NOT_ALLOWED),
        (URL_SIGNUP, ANONYMOUS_CLIENT, HTTPStatus.OK),
    )
)
def test_pages_availability_for_different_users(
    url, _client, status
):
    """
    Тестирует доступность различных URL адресов для
    разных пользователей (анонимных, авторов, читателей) по GET запросу
    Args:
    url: URL адрес, который нужно проверить;
    _client: Клиент для выполнения запроса (анонимный, автор, читатель);
    status: Ожидаемый HTTP статус ответа
    """
    assert _client.get(url).status_code == status


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url, parametrized_client, expected_status',
    (
        (URL_COMMENT_DELETE, AUTHOR_CLIENT, HTTPStatus.OK),
        (URL_COMMENT_DELETE, READER_CLIENT, HTTPStatus.NOT_FOUND),
        (URL_COMMENT_EDIT, AUTHOR_CLIENT, HTTPStatus.OK),
        (URL_COMMENT_EDIT, READER_CLIENT, HTTPStatus.NOT_FOUND),
    )
)
def test_availability_edit_delete_for_author_and_reader(
    url, parametrized_client, expected_status
):
    """
    Тестирует доступность страниц редактирования и удаления комментариев
    для автора (ожидаем 200) и для другого пользователя (ожидаем 302)
    """
    response = parametrized_client.get(url)
    if expected_status == HTTPStatus.OK:
        assert response.status_code == expected_status
    elif expected_status == HTTPStatus.NOT_FOUND:
        assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize("url", [URL_COMMENT_DELETE, URL_COMMENT_EDIT])
def test_availability_pages_edit_delete_for_anonymous_user(
    client, url
):
    """
    При попытке перейти на страницу редактирования
    или удаления комментария анонимный пользователь
    перенаправляется на страницу авторизации
    """
    expected_url = f'{reverse("users:login")}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
