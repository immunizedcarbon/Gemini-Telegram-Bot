"""Access helpers for the Bundestag DIP API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict
from urllib.parse import urlencode

import aiohttp

from config import conf

logger = logging.getLogger(__name__)

BASE_URL = "https://search.dip.bundestag.de/api/v1"


async def _request(session: aiohttp.ClientSession, path: str, params: Dict[str, Any]) -> Any:
    """Make a GET request to the DIP API and return JSON."""
    params = {k: v for k, v in params.items() if v is not None}
    if conf.dip_api_key:
        params.setdefault("apikey", conf.dip_api_key)
    url = f"{BASE_URL}/{path}?{urlencode(params)}"
    logger.debug("DIP request %s", url)
    async with session.get(url, headers={"Accept": "application/json"}) as resp:
        resp.raise_for_status()
        return await resp.json()


async def fetch_entity(resource: str, entity_id: str) -> Any:
    """Fetch a single entity by ID."""
    async with aiohttp.ClientSession() as session:
        return await _request(session, f"{resource}/{entity_id}", {})


async def search(resource: str, **params: Any) -> Any:
    """Search for entities of ``resource`` type using query parameters."""
    async with aiohttp.ClientSession() as session:
        return await _request(session, resource, params)


async def dip_fetch(resource: str, id: str) -> Any:
    """Return JSON data for a single item from the DIP API.

    Parameters
    ----------
    resource: str
        Resource name such as ``vorgang`` or ``drucksache``.
    id: str
        Identifier of the item to fetch.
    """

    return await fetch_entity(resource, id)


async def dip_search(resource: str, params: Dict[str, str] | None = None) -> Any:
    """Search the DIP API and return JSON results.

    Parameters
    ----------
    resource: str
        Resource name to search.
    params: dict[str, str] | None
        Optional query parameters as defined by the DIP API.
    """

    return await search(resource, **(params or {}))
