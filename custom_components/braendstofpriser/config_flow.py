"""Config flow for braendstofpriser integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aiohttp import ClientResponseError
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers.event import async_call_later
from pybraendstofpriser import Braendstofpriser

from . import async_setup_entry, async_unload_entry
from .const import CONF_COMPANY, CONF_PRODUCTS, CONF_STATION, DOMAIN

_LOGGER = logging.getLogger(__name__)


class BraendstofpriserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for braendstofpriser."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> BraendstofpriserOptionsFlow:
        """Get the options flow for this handler."""
        return BraendstofpriserOptionsFlow()

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api: Braendstofpriser
        self.companies = {}
        self.stations = {}
        self.company_name = ""
        self._errors = {}
        self.user_input = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step - Enter API key."""
        if user_input is not None:
            # Test API key
            try:
                # Initialize API
                self.api = Braendstofpriser(user_input[CONF_API_KEY])
                self.companies = await self.api.list_companies()
            except ClientResponseError as exc:  # pylint: disable=broad-except
                if exc.status == 401:
                    self._errors["base"] = "invalid_api_key"
                    return self.async_abort(reason="invalid_api_key")

            # Proceed to company selection
            self.user_input.update(user_input)
            return await self.async_step_company_selection()

        # Show the form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=self._errors,
        )

    async def async_step_company_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the company selection step."""
        if user_input is not None:
            # Process the user input and show next selection form
            self.company_name = user_input[CONF_COMPANY]
            self.user_input.update(user_input)
            return await self.async_step_station_selection()

        # Show the form to the user
        return self.async_show_form(
            step_id="company_selection",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COMPANY): vol.In(
                        [c["name"] for _, c in self.companies.items()]
                    ),
                }
            ),
            errors=self._errors,
        )

    async def async_step_station_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the station selection step."""
        if user_input is not None:
            # Match station name to station ID
            for key, station in self.stations.items():
                if station["name"] == user_input[CONF_STATION]:
                    user_input[CONF_STATION] = key
                    break

            # Set UniqueID and abort if already existing
            await self.async_set_unique_id(
                f"{self.user_input[CONF_COMPANY]}_{user_input[CONF_STATION]}"
            )
            self._abort_if_unique_id_configured()

            # Process the user input and show next selection form
            self.user_input.update(user_input)
            return await self.async_step_product_selection()

        def sorter(e):
            return e.name

        # Get station list, sort it and make a list with only names
        self.stations = await self.api.list_stations(company_name=self.company_name)
        self.stations = {
            k: v
            for k, v in sorted(self.stations.items(), key=lambda item: item[1]["name"])
        }
        stations = list(s["name"] for _, s in self.stations.items())

        # Show the form to the user
        return self.async_show_form(
            step_id="station_selection",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION): vol.In(list(stations)),
                }
            ),
            errors=self._errors,
        )

    async def async_step_product_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the product selection step."""
        if user_input is not None:
            # Process the user input and create the device
            # Create the device entry
            config_options = {
                CONF_PRODUCTS: user_input,
                CONF_API_KEY: self.user_input[CONF_API_KEY],
            }

            return self.async_create_entry(
                title=f"{self.user_input[CONF_COMPANY]}",
                data={
                    CONF_COMPANY: self.user_input[CONF_COMPANY],
                    CONF_STATION: self.user_input[CONF_STATION],
                },
                description=f"{self.user_input[CONF_COMPANY]}, {self.stations[self.user_input[CONF_STATION]]['name']}",
                options=config_options,
            )

        # Get available products and translate the system names to human readable
        products_available = await self.api.get_prices(self.user_input[CONF_STATION])

        # Create a list of available products
        schema = {}
        for prod in products_available["prices"].keys():
            schema.update({vol.Required(prod): bool})

        # Show the form to the user
        return self.async_show_form(
            step_id="product_selection",
            data_schema=vol.Schema(schema),
            errors=self._errors,
        )


class BraendstofpriserOptionsFlow(config_entries.OptionsFlow):
    """Handle a options flow for braendstofpriser."""

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api: Braendstofpriser = Braendstofpriser()
        self.companies = None
        self._errors = {}
        self.user_input = {}

    async def _do_update(
        self, *args, **kwargs  # pylint: disable=unused-argument
    ) -> None:
        """Update after settings change."""
        await async_unload_entry(self.hass, self.config_entry)
        await async_setup_entry(self.hass, self.config_entry)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        # self.companies = await self.api.list_companies()
        company = self.config_entry.data[CONF_COMPANY]
        await self.api.set_company(company)

        if user_input is not None:
            p_list = {}
            for product, selected in user_input.items():
                for prod_key, prod_val in self.companies[self.user_input[CONF_COMPANY]][
                    "products"
                ].items():
                    if prod_val["name"] == product:
                        p_list.update({prod_key: selected})

            async_call_later(self.hass, 2, self._do_update)

            return self.async_create_entry(
                title=self.user_input[CONF_COMPANY],
                data=p_list,
            )

        station = self.config_entry.data[CONF_STATION]

        # Get available products and translate the system names to human readable
        products_available = await self.api.list_products(self.user_input[CONF_STATION])
        product_names = self.companies[self.user_input[CONF_COMPANY]]["products"]
        product_list = list(product_names[p]["name"] for p in products_available)
        product_list.sort()

        # Create a list of available products
        schema = {}
        for prod in product_list:
            schema.update({vol.Required(prod): bool})

        prod_list = list(
            [k, v["name"]] for k, v in self.companies[company]["products"].items()
        )
        schema = {}
        for prod in prod_list:
            schema.update(
                {
                    vol.Required(
                        prod[1], default=self.config_entry.options.get(prod[0], False)
                    ): bool
                }
            )

        self.user_input.update({CONF_COMPANY: company})

        # Show the form to the user
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
