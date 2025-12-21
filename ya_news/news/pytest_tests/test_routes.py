from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

LOGIN_URL = reverse("users:login")


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('pk_for_args')),
        ('news:home', None),
        ('users:login', None),
        ('users:signup', None),

    )
)
def test_pages_availability_get_anonymous(client, name, args):
    response = client.get(reverse(name, args=args))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    "client_fixture_name, expected_status",
    (
        (pytest.lazy_fixture('auth_client'), HTTPStatus.OK),
        (pytest.lazy_fixture('reader_client'), HTTPStatus.NOT_FOUND)
    ),
)
@pytest.mark.parametrize('name', ('news:edit', 'news:delete'))
def test_availability_pages_edit_delete_for_author_and_reader(
    client_fixture_name, expected_status, comment, name
):
    response = client_fixture_name.get(reverse(name, args=(comment.pk,)))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete')
)
def test_availability_pages_edit_delete_for_anonymous_user(
    client, comment, name
):
    url = reverse(name, args=(comment.pk,))
    expected_url = f'{LOGIN_URL}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
