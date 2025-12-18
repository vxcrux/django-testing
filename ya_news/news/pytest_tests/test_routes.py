from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

LOGIN_URL = reverse("users:login")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name, args",
    (
        ("news:detail", pytest.lazy_fixture("pk_for_args")),
        ("news:home", None),
        ("users:login", None),
        ("users:signup", None),
    ),
)
def test_pages_availability_get_anonymous(client, name, args):
    """
    Проверяет, что страницы news:detail, news:home, users:login, users:signup
    доступны анонимному пользователю по GET-запросу
    """
    response = client.get(reverse(name, args=args))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_logout_page_behavior_anonymous(client):
    """
    Проверяет поведение users:logout для анонимного пользователя:
    GET-запрос должен вернуть 405 Method Not Allowed
    POST-запрос должен перенаправлять на страницу логина
    """
    logout_url = reverse("users:logout")

    response_get = client.get(logout_url)
    assert response_get.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    response_post = client.post(logout_url)
    expected_redirect_url = reverse("users:login")
    assertRedirects(response_post, expected_redirect_url)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "parametrized_client, expected_status",
    (
        (pytest.lazy_fixture("auth_client"), HTTPStatus.OK),
        (pytest.lazy_fixture("another_author"), HTTPStatus.NOT_FOUND),
    ),
)
@pytest.mark.parametrize("name", ("news:edit", "news:delete"))
def test_availability_pages_edit_delete_for_author_and_reader(
    parametrized_client, expected_status, comment, name
):
    """
    Авторизованный пользователь не может зайти
    на страницы редактирования или
    удаления чужих комментариев (возвращается ошибка 404)
    """
    response = parametrized_client.get(reverse(name, args=(comment.pk,)))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize("name", ("news:edit", "news:delete"))
def test_availability_pages_edit_delete_for_anonymous_user(
        client, comment, name):
    """
    При попытке перейти на страницу редактирования
    или удаления комментария анонимный пользователь
    перенаправляется на страницу авторизации
    """
    url = reverse(name, args=(comment.pk, ))
    expected_url = f"{LOGIN_URL}?next={url}"
    response = client.get(url)
    assertRedirects(response, expected_url)
