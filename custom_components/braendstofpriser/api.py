"""API for Braendstofpriser integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pybraendstofpriser import Braendstofpriser
from pybraendstofpriser.exceptions import ProductNotFoundError

from .const import CONF_COMPANY, CONF_PRODUCTS, CONF_STATION, DOMAIN

SCAN_INTERVAL = timedelta(hours=1)

_LOGGER = logging.getLogger(__name__)

type BraendstofpriserConfigEntry = ConfigEntry[APIClient]


class APIClient(DataUpdateCoordinator[None]):
    """DataUpdateCoordinator for Braendstofpriser."""

    def __init__(
        self,
        hass,
    ) -> None:
        """Initialize the API client."""
        DataUpdateCoordinator.__init__(
            self,
            hass=hass,
            name=DOMAIN,
            logger=_LOGGER,
            update_interval=SCAN_INTERVAL,
        )

        self._api = Braendstofpriser(self.config_entry.options.get(CONF_API_KEY))
        self._hass = hass
        self.company: str = self.config_entry.data.get(CONF_COMPANY)
        self.station_id: int = int(self.config_entry.data.get(CONF_STATION))
        self.station_name: str = ""
        self._products: dict = self.config_entry.options.get(CONF_PRODUCTS, {})
        self.products = {}
        self._last_data: dict = {}
        self.previous_devices: set[str] = set()
        self.updated_at: datetime | None = None

        self.name = self.company

    async def _async_setup(self) -> None:
        """Initialize the API client."""
        _LOGGER.debug("Selected products: %s", self._products)
        for product, selected in self._products.items():
            if selected:
                self.products.update(
                    {
                        product: {
                            "name": product,
                            "price": None,
                        }
                    }
                )

    async def _async_update_data(self) -> None:
        """Handle data update request from the coordinator."""

        self._last_data = await self._api.get_prices(self.station_id)
        self.station_name = self._last_data["station"]["name"]
        self.updated_at = (
            datetime.fromisoformat(self._last_data["station"]["last_update"])
            if not isinstance(self._last_data["station"]["last_update"], type(None))
            else None
        )
        try:
            for product in self.products:
                _LOGGER.debug(
                    "Getting price for %s",
                    product,
                )
                self.products[product]["price"] = self._last_data["prices"].get(product)
                _LOGGER.debug(
                    "Updated price for %s: %s",
                    self.products[product]["name"],
                    self._last_data["prices"].get(product),
                )
                _LOGGER.debug(
                    "Updated at: %s",
                    self._last_data["station"].get("last_update", "UNKNOWN"),
                )
        except ProductNotFoundError as exc:
            raise ConfigEntryError(exc)
