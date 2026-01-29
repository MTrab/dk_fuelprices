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
        self, hass, api_key: str, company: str, station: dict, products: dict
    ) -> None:
        """Initialize the API client."""
        DataUpdateCoordinator.__init__(
            self,
            hass=hass,
            name=DOMAIN,
            logger=_LOGGER,
            update_interval=SCAN_INTERVAL,
        )
        # if self.config_entry is None:
        #     self.config_entry = config_entry

        self._api = Braendstofpriser(api_key)
        self._hass = hass
        self.company: str = company
        self.station_id: int = station["id"]
        self.station_name: str = station["name"]
        self._products: dict = products
        self.products = {}
        self.previous_devices: set[str] = set()
        self.updated_at: datetime | None = None
        self.stations = None

        self.name = self.company

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

    async def _async_setup(self) -> None:
        """Initialize the API client."""
        # data = await self._api.get_prices(self.station_id)
        # self.station_name = data["station"]["name"]
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
        data = await self._api.get_prices(self.station_id)
        self.station_name = data["station"]["name"]
        self.updated_at = (
            datetime.fromisoformat(data["station"]["last_update"])
            if not isinstance(data["station"]["last_update"], type(None))
            else None
        )
        try:
            for product in self.products:
                _LOGGER.debug(
                    "Getting price for %s",
                    product,
                )
                self.products[product]["price"] = data["prices"].get(product)
                _LOGGER.debug(
                    "Updated price for %s: %s",
                    self.products[product]["name"],
                    data["prices"].get(product),
                )
                _LOGGER.debug(
                    "Updated at: %s",
                    data["station"].get("last_update", "UNKNOWN"),
                )
        except ProductNotFoundError as exc:
            raise ConfigEntryError(exc)
