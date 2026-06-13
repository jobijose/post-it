"""Tests for draft and LinkedIn publishers."""

from __future__ import annotations

import pytest

from post_it.exceptions import AuthError, PublishError
from post_it.models import ApprovedPost, PostVariant
from post_it.publishers.base import SocialPublisher
from post_it.publishers.draft import DraftPublisher
from post_it.publishers.linkedin import LinkedInPublisher


def _approved(text="Hello world", platform="linkedin"):
    return ApprovedPost(
        variant=PostVariant(index=1, angle="punchy", text=text), platform=platform
    )


def test_draft_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(DraftPublisher, "_copy_to_clipboard", staticmethod(lambda t: False))
    pub = DraftPublisher(draft_dir=tmp_path)
    result = pub.publish(_approved())
    assert result.success
    assert result.location.endswith(".txt")
    from pathlib import Path

    assert "Hello world" in Path(result.location).read_text()


def test_validate_rejects_empty(tmp_path):
    pub = DraftPublisher(draft_dir=tmp_path)
    with pytest.raises(PublishError):
        pub.publish(_approved(text="   "))


def test_validate_rejects_over_length():
    class _P(SocialPublisher):
        name = "x"

        def publish(self, approved):
            ...

    with pytest.raises(PublishError):
        _P().validate("a" * 3001, platform="linkedin")


def test_linkedin_publish_success(httpx_mock):
    httpx_mock.add_response(
        url="https://api.linkedin.com/rest/posts",
        status_code=201,
        headers={"x-restli-id": "urn:li:share:123"},
        json={},
    )
    pub = LinkedInPublisher(
        access_token="tok", author_urn="urn:li:person:abc", api_version="202505"
    )
    result = pub.publish(_approved())

    assert result.success
    assert "urn:li:share:123" in result.location
    request = httpx_mock.get_requests()[0]
    assert request.headers["LinkedIn-Version"] == "202505"
    assert request.headers["X-Restli-Protocol-Version"] == "2.0.0"
    assert request.headers["Authorization"] == "Bearer tok"


def test_linkedin_401_maps_to_auth_error(httpx_mock):
    httpx_mock.add_response(
        url="https://api.linkedin.com/rest/posts",
        status_code=401,
        json={"message": "expired"},
    )
    pub = LinkedInPublisher(access_token="tok", author_urn="urn:li:person:abc")
    with pytest.raises(AuthError):
        pub.publish(_approved())


def test_linkedin_403_maps_to_auth_error(httpx_mock):
    httpx_mock.add_response(
        url="https://api.linkedin.com/rest/posts",
        status_code=403,
        json={"message": "no scope"},
    )
    pub = LinkedInPublisher(access_token="tok", author_urn="urn:li:person:abc")
    with pytest.raises(AuthError):
        pub.publish(_approved())


def test_linkedin_requires_token():
    with pytest.raises(AuthError):
        LinkedInPublisher(access_token="", author_urn="urn:li:person:abc")
