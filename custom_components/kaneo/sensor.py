"""Sensor platform for Kaneo integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_TASKS_LIST,
    ATTR_TOTAL_TASKS,
    CONF_WORKSPACE_ID,
    DOMAIN,
)
from .coordinator import KaneoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kaneo sensors from a config entry."""
    coordinator: KaneoDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    workspace_id = config_entry.data[CONF_WORKSPACE_ID]

    async_add_entities(
        [
            KaneoTasksSensor(coordinator, workspace_id, config_entry.entry_id),
        ]
    )


class KaneoTasksSensor(CoordinatorEntity[KaneoDataUpdateCoordinator], SensorEntity):
    """Sensor representing all Kaneo tasks."""

    _attr_icon = "mdi:checkbox-marked-outline"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KaneoDataUpdateCoordinator,
        workspace_id: str,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._workspace_id = workspace_id
        self._attr_unique_id = f"kaneo_{entry_id}_tasks"
        self._attr_name = "Tâches"

    @property
    def native_value(self) -> int:
        """Return total number of tasks."""
        if self.coordinator.data is None:
            return 0
        return len(self.coordinator.data)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "tâches"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes with full task list."""
        if self.coordinator.data is None:
            return {ATTR_TOTAL_TASKS: 0, ATTR_TASKS_LIST: []}

        tasks = self.coordinator.data
        simplified_tasks = []
        for task in tasks:
            simplified_tasks.append(
                {
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "status": task.get("_column_name"),
                    "priority": task.get("priority"),
                    "due_date": task.get("dueDate"),
                    "project": task.get("_project_name"),
                    "assignee": _extract_assignee(task),
                    "created_at": task.get("createdAt"),
                    "description": task.get("description"),
                    "number": task.get("number"),
                }
            )

        return {
            ATTR_TOTAL_TASKS: len(tasks),
            ATTR_TASKS_LIST: simplified_tasks,
        }

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._workspace_id)},
            "name": f"Kaneo Workspace {self._workspace_id}",
            "manufacturer": "Kaneo",
            "model": "Task Manager",
            "configuration_url": "https://kaneo.app",
        }


def _extract_assignee(task: dict[str, Any]) -> str | None:
    """Extract assignee name from task data."""
    assignee = task.get("assignee")
    if not assignee:
        return None
    if isinstance(assignee, dict):
        return assignee.get("name") or assignee.get("email")
    return str(assignee)
