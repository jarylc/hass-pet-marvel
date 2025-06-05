# Pet Marvel Integration for Home Assistant 🏠

[![GitHub Release](https://img.shields.io/github/v/release/jarylc/hass-pet-marvel?sort=semver&style=for-the-badge&color=green)](https://github.com/jarylc/hass-pet-marvel/releases/)
[![GitHub Release Date](https://img.shields.io/github/release-date/jarylc/hass-pet-marvel?style=for-the-badge&color=green)](https://github.com/jarylc/hass-pet-marvel/releases/)
![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/jarylc/hass-pet-marvel/latest/total?style=for-the-badge&label=Downloads%20latest%20Release)
![HA Analytics](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.pet_marvel.total&style=for-the-badge&label=Active%20Installations&color=red)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/jarylc/hass-pet-marvel?style=for-the-badge)
[![hacs](https://img.shields.io/badge/HACS-Integration-blue.svg?style=for-the-badge)](https://github.com/hacs/integration)

## Overview
The Pet Marvel Home Assistant Custom Integration allows you to integrate your Pet Marvel devices with your Home Assistant setup.

### Currently supported devices
- Pet Marvel C1 (Cat Litter Box)

### Currently supported features
#### Sensors:
| Sensor           | Unit                                                                                                                                        | Example Value    | Enabled by default |
|------------------|---------------------------------------------------------------------------------------------------------------------------------------------|------------------|--------------------|
| Status           | idle / cleaning / cleaning_complete / dumping / dumping_complete / resetting / resetting_complete / paused / cat_approaching / cat_entering | idle             | yes                |
| Last usage       | datetime                                                                                                                                    | 2024-12-07 14:52 | yes                |
| Error status     | normal / motor_failure / magnet_clean_abnormal / magnet_idle_abnormal / weight_abnormal / weight_high                                       | normal           | yes                |
| Software version | version                                                                                                                                     | mcu-082          | no (debug)         |

#### Binary sensors:
| Binary Sensor | Example Value | Enabled by default |
|---------------|---------------|--------------------|
| Lid installed | on            | yes                |
| Bin inserted  | on            | yes                |
| Bin full      | off           | yes                |

#### Buttons:
| Button | Action                                                         | Enabled by default     |
|--------|----------------------------------------------------------------|------------------------|
| Clean  | Cleans the litter box                                          | yes                    |
| Level  | Initiates the leveling process                                 | yes                    |
| Dump   | Dump all litter (be reminded to remove the protective casing)  | no (prevent accidents) |

#### Switches:
| Switch         | Enabled by default |
|----------------|--------------------|
| Auto clean     | yes                |
| Auto bury      | yes                |
| Device lights  | yes                |
| Small cat mode | no (rare scenario) |

## Installation

### HACS (recommended)
This integration is available in HACS (Home Assistant Community Store).

1. Install HACS if you don't have it already
2. Open HACS in Home Assistant
3. Go to any of the sections (integrations, frontend, automation).
4. Click on the 3 dots in the top right corner.
5. Select "Custom repositories"
6. Add following URL to the repository `https://github.com/jarylc/hass-pet-marvel`.
7. Select Integration as category.
8. Click the "ADD" button
9. Search for "Pet Marvel"
10. Click the "Download" button

### Manual installation
#### From downloaded zip archive
To install this integration manually you have to download [_pet_marvel.zip_](https://github.com/jarylc/hass-pet-marvel/releases/latest/) and extract its contents to `config/custom_components/pet_marvel` directory:

```bash
mkdir -p custom_components/pet_marvel
cd custom_components/pet_marvel
wget https://github.com/jaryl/hass-pet-marvel/releases/latest/download/pet_marvel.zip
unzip pet_marvel.zip
rm pet_marvel.zip
```

Restart Home Assistant.

#### Installation from git repository
With this variant, you can easily update the integration from the github repository.

##### First installation:
```bash
cd <to your Home Assistant config directory>
git clone https://github.com/jarylc/hass-pet-marvel
mkdir custom_components
cd custom_components
ln -s ../hass-pet-marvel/custom_components/pet_marvel/ .
```

Restart Home Assistant.

##### update the existing installation:
```bash
cd <to your Home Assistant config directory>
cd hass-pet-marvel/
git pull
```

Restart Home Assistant.

## Configuration
### Using UI
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=pet_marvel)

From the Home Assistant front page go to `Configuration` and then select `Devices & Services` from the list.
Use the `Add Integration` button in the bottom right to add a new integration called `Pet Marvel`.

## Troubleshooting Tips / Known Issues
1. When you discover that the mobile app is starting over and over, beginning again with the login steps, then you should use this HA integration with a different account than with the app. Create a second account and use the share function in the app - simply share the device with the second account
2. Power-cycle the litterbox
3. Reset the litterbox and re-integrate it
4. Open an issue

## Help and Contribution
If you find a problem, feel free to report it and I will do my best to help you.
If you have something to contribute, your help is greatly appreciated!
If you want to add a new feature, add a pull request first so we can discuss the details.

## Disclaimer
This custom integration is not officially endorsed or supported by Pet Marvel.
Use it at your own risk and ensure that you comply with all relevant terms of service and privacy policies.
