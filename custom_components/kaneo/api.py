"""Kaneo API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    API_PROJECTS,
    API_SESSION,
    API_TASKS,
)

_LOGGER = logging.getLogger(__name__)


class KaneoApiError(Exception):
    """Generic API error."""


class KaneoAuthError(KaneoApiError):
    """Authentication error."""


class KaneoConnectionError(KaneoApiError):
    """Connection error."""


class KaneoApiClient:
    """Kaneo API client."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        workspace_id: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._workspace_id = workspace_id
        self._session = session

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        """Make an API request."""
        url = f"{self._base_url}{endpoint}"
        try:
            async with self._session.request(
                method, url, headers=self._headers, **kwargs
            ) as response:
                if response.status == 401:
                    raise KaneoAuthError("Invalid API token")
                if response.status == 403:
                    raise KaneoAuthError("Access forbidden")
                if response.status >= 400:
                    text = await response.text()
                    raise KaneoApiError(f"API error {response.status}: {text}")
                return await response.json()
        except aiohttp.ClientConnectorError as err:
            raise KaneoConnectionError(f"Cannot connect to {self._base_url}") from err
        except aiohttp.ClientError as err:
            raise KaneoApiError(f"Request failed: {err}") from err

    async def validate_auth(self) -> bool:
        """Validate authentication by calling get-session."""
        try:
            await self._request("GET", API_SESSION)
            return True
        except KaneoAuthError:
            return False

    async def get_projects(self) -> list[dict[str, Any]]:
        """Get all projects in the workspace."""
        return await self._request(
            "GET",
            API_PROJECTS,
            params={"workspaceId": self._workspace_id},
        )

    async def get_tasks(self, project_id: str) -> dict[str, Any]:
        """Get all tasks for a project."""
        endpoint = API_TASKS.format(project_id=project_id)
        return await self._request("GET", endpoint)

    async def get_all_tasks(self) -> list[dict[str, Any]]:
        """Get all tasks across all projects."""
        all_tasks: list[dict[str, Any]] = []

        try:
            projects = await self.get_projects()
        except KaneoApiError as err:
            _LOGGER.error("Failed to fetch projects: %s", err)
            return all_tasks

        for project in projects:
            project_id = project.get("id")
            project_name = project.get("name", "Unknown")
            if not project_id:
                continue

            try:
                data = await self.get_tasks(project_id)
                # The API returns { columns: [{ tasks: [...] }] } or similar
                columns = data.get("columns", [])
                for column in columns:
                    tasks = column.get("tasks", [])
                    for task in tasks:
                        task["_project_name"] = project_name
                        task["_project_id"] = project_id
                        task["_column_name"] = column.get("name", "")
                        all_tasks.append(task)
            except KaneoApiError as err:
                _LOGGER.warning(
                    "Failed to fetch tasks for project %s: %s", project_name, err
                )

        return all_tasks
