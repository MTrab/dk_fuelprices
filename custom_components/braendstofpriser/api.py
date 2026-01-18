"""API for Braendstofpriser integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pybraendstofpriser import Braendstofpriser
from pybraendstofpriser.exceptions import ProductNotFoundError

from .const import DOMAIN

SCAN_INTERVAL = timedelta(hours=1)

_LOGGER = logging.getLogger(__name__)

type BraendstofpriserConfigEntry = ConfigEntry[APIClient]


class APIClient(DataUpdateCoordinator[None]):
    """DataUpdateCoordinator for Braendstofpriser."""

    def __init__(self, hass, company: str, station: str, products) -> None:
        """Initialize the API client."""
        DataUpdateCoordinator.__init__(
            self,
            hass=hass,
            name=DOMAIN,
            logger=_LOGGER,
            update_interval=SCAN_INTERVAL,
        )

        self._api = Braendstofpriser()
        self._hass = hass
        self.company = company
        self.station = station
        self._products = products
        self.products = {}

        self.previous_devices: set[str] = set()

    async def _async_setup(self) -> None:
        """Initialize the API client."""
        await self._api.set_company(self.company)
        _LOGGER.debug("Selected products: %s", self._products)
        for product, selected in self._products.items():
            if selected:
                self.products.update(
                    {
                        product: {
                            "name": self._api.company.get_product_name(product),
                            "price": None,
                        }
                    }
                )

    async def _async_update_data(self) -> None:
        """Handle data update request from the coordinator."""

        try:
            for product in self.products:
                _LOGGER.debug(
                    "Getting price for %s at %s, %s",
                    product,
                    self.company,
                    self.station,
                )
                price = self._api.get_price(
                    self.station,
                    product,
                )
                self.products[product]["price"] = price
                _LOGGER.debug(
                    "Updated price for %s, %s, %s: %s",
                    self.company,
                    self.station,
                    self.products[product]["name"],
                    price,
                )
        except ProductNotFoundError as exc:
            raise ConfigEntryError(exc)
