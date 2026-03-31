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

    async def get_tasks(self, project_id: str) -> Any:
        """Get all tasks for a project (raw response)."""
        endpoint = API_TASKS.format(project_id=project_id)
        return await self._request("GET", endpoint)

    def _extract_tasks_from_response(
        self,
        data: Any,
        project_name: str,
        project_id: str,
    ) -> list[dict[str, Any]]:
        """
        Extract a flat task list from whatever structure the API returns.

        Kaneo may return one of several shapes:
          1. { "columns": [ { "name": "...", "tasks": [...] } ] }
          2. { "tasks": [...] }
          3. [ { "id": "...", "title": "..." }, ... ]   (flat list)
          4. A task object directly (unlikely but handled)
        """
        tasks: list[dict[str, Any]] = []

        _LOGGER.debug(
            "Raw tasks response for project '%s' (type=%s): %s",
            project_name,
            type(data).__name__,
            data,
        )

        if data is None:
            _LOGGER.warning("Null response for project '%s'", project_name)
            return tasks

        # Case 3 — flat list at top level
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    item.setdefault("_project_name", project_name)
                    item.setdefault("_project_id", project_id)
                    item.setdefault("_column_name", item.get("status", ""))
                    tasks.append(item)
            return tasks

        if not isinstance(data, dict):
            _LOGGER.warning(
                "Unexpected response type for project '%s': %s", project_name, type(data)
            )
            return tasks

        # Case 1 — { columns: [{ name, tasks }] }
        if "columns" in data:
            for column in data["columns"]:
                col_name = column.get("name", column.get("title", ""))
                for task in column.get("tasks", []):
                    if isinstance(task, dict):
                        task["_project_name"] = project_name
                        task["_project_id"] = project_id
                        task["_column_name"] = col_name
                        tasks.append(task)
            return tasks

        # Case 2 — { tasks: [...] }
        if "tasks" in data:
            for task in data["tasks"]:
                if isinstance(task, dict):
                    task["_project_name"] = project_name
                    task["_project_id"] = project_id
                    task["_column_name"] = task.get("status", "")
                    tasks.append(task)
            return tasks

        # Case 4 — the dict itself looks like a project wrapper containing task data
        # Try every key whose value is a list and pick the one with task-like dicts
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                if "id" in value[0] or "title" in value[0]:
                    _LOGGER.debug(
                        "Found tasks under key '%s' for project '%s'", key, project_name
                    )
                    for task in value:
                        if isinstance(task, dict):
                            task["_project_name"] = project_name
                            task["_project_id"] = project_id
                            task["_column_name"] = task.get("status", "")
                            tasks.append(task)
                    return tasks

        _LOGGER.warning(
            "Could not extract tasks from response keys %s for project '%s'",
            list(data.keys()),
            project_name,
        )
        return tasks

    async def get_all_tasks(self) -> list[dict[str, Any]]:
        """Get all tasks across all projects."""
        all_tasks: list[dict[str, Any]] = []

        try:
            projects = await self.get_projects()
        except KaneoApiError as err:
            _LOGGER.error("Failed to fetch projects: %s", err)
            return all_tasks

        _LOGGER.debug("Found %d projects", len(projects))

        for project in projects:
            project_id = project.get("id")
            project_name = project.get("name", "Unknown")
            if not project_id:
                continue

            try:
                data = await self.get_tasks(project_id)
                project_tasks = self._extract_tasks_from_response(
                    data, project_name, project_id
                )
                _LOGGER.debug(
                    "Project '%s': extracted %d tasks", project_name, len(project_tasks)
                )
                all_tasks.extend(project_tasks)
            except KaneoApiError as err:
                _LOGGER.warning(
                    "Failed to fetch tasks for project '%s': %s", project_name, err
                )

        _LOGGER.debug("Total tasks fetched: %d", len(all_tasks))
        return all_tasks
