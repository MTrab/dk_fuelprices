![Current Release](https://img.shields.io/github/release/mtrab/braendstofpriser/all.svg?style=plastic)
![Github All Releases](https://img.shields.io/github/downloads/mtrab/braendstofpriser/total.svg?style=plastic)
<!--![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=plastic)-->


<a href="https://www.buymeacoffee.com/mtrab" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

This integration will provide fuel prices from the companies in Denmark that are publishing prices to their webpages.<br>
Not all companies does this, thus not all companies are available in the integration.

If you stumble across a company providing public prices, that are not available in the integration, [please create an issue providing the full URL to the webpage showing the prices](https://github.com/MTrab/pybraendstofpriser/issues/new).

## Table of Content

[**Installation**](#installation)

[**Setup**](#setup)

[**Currently supported companies**](#currently-supported-companies)
 

## Installation:

Aquire your free API key from https://fuelprices.dk - it is required for this integration

~~### Option 1 (easy) - HACS:~~

*   ~~Ensure that HACS is installed.~~
*   ~~Search for and install the "Brændstofpriser" integration.~~
*   ~~Restart Home Assistant.~~

### Option 2 - Add custom repository to HACS:

*   See [this link](https://www.hacs.xyz/docs/faq/custom_repositories/) for how to add a custom repository to HACS.
*   Add `https://github.com/MTrab/braendstofpriser` as custom repository of type Integration
*   Search for and install the "Brændstofpriser" integration.
*   Restart Home Assistant.

### Option 3 - Manual installation:

*   Download the latest release.
*   Unpack the release and copy the custom\_components/braendstofpriser directory into the custom\_components directory of your Home Assistant installation.
*   Restart Home Assistant.

## Setup

My Home Assistant shortcut:

[![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=braendstofpriser)

Or go to Home Assistant > Settings > Integrations

Add "Brændstofpriser" integration _(If it doesn't show, try CTRL+F5 to force a refresh of the page)_

## Currently supported companies

The supported companies can be seen on https://fuelprices.dk
