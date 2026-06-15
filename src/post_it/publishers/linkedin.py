"""LinkedIn publisher — posts via the modern Posts API (``/rest/posts``)."""

from __future__ import annotations

from typing import ClassVar

import httpx

from post_it.exceptions import AuthError, PublishError
from post_it.models import ApprovedPost, PublishResult
from post_it.publishers.base import SocialPublisher
from post_it.publishers.linkedin_oauth import fetch_author_urn

POSTS_URL = "https://api.linkedin.com/rest/posts"


class LinkedInPublisher(SocialPublisher):
    name: ClassVar[str] = "linkedin"

    def __init__(
        self,
        *,
        access_token: str,
        author_urn: str | None = None,
        api_version: str = "202505",
    ) -> None:
        if not access_token:
            raise AuthError(
                "No LinkedIn access token. Run `post-it auth linkedin` first."
            )
        self.access_token = access_token
        self.api_version = api_version
        # Author URN can be cached in config; otherwise resolve it from the token.
        self.author_urn = author_urn or fetch_author_urn(access_token)

    def publish(self, approved: ApprovedPost) -> PublishResult:
        text = approved.variant.text
        self.validate(text, platform="linkedin")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
        }
        body = {
            "author": self.author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        try:
            resp = httpx.post(POSTS_URL, headers=headers, json=body, timeout=20.0)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise self._map_error(exc) from exc
        except httpx.HTTPError as exc:
            raise PublishError(f"Failed to reach LinkedIn: {exc}") from exc

        post_id = resp.headers.get("x-restli-id") or resp.headers.get("x-linkedin-id")
        location = (
            f"https://www.linkedin.com/feed/update/{post_id}" if post_id else None
        )
        return PublishResult(
            mode="linkedin",
            success=True,
            location=location,
            detail=f"Published to LinkedIn (id: {post_id}).",
        )

    @staticmethod
    def _map_error(exc: httpx.HTTPStatusError) -> Exception:
        status = exc.response.status_code
        try:
            detail = exc.response.json().get("message", exc.response.text)
        except Exception:
            detail = exc.response.text
        if status == 401:
            return AuthError(f"LinkedIn token expired or invalid: {detail}")
        if status == 403:
            return AuthError(
                f"Missing 'w_member_social' permission or app not approved: {detail}"
            )
        if status == 429:
            return PublishError(f"LinkedIn rate limit hit: {detail}")
        return PublishError(f"LinkedIn rejected the post ({status}): {detail}")
