"""Data update coordinator for Kaneo."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KaneoApiClient, KaneoApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KaneoDataUpdateCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator to fetch Kaneo tasks periodically."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: KaneoApiClient,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch data from Kaneo API."""
        try:
            tasks = await self.client.get_all_tasks()
            _LOGGER.debug("Fetched %d tasks from Kaneo", len(tasks))
            return tasks
        except KaneoApiError as err:
            raise UpdateFailed(f"Error communicating with Kaneo API: {err}") from err
