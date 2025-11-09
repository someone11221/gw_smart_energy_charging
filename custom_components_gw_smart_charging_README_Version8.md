# GW Smart Charging (integration folder)

This folder contains the Home Assistant custom integration. After installation via HACS,
the folder will be placed under `/config/custom_components/gw_smart_charging/`.

Files:
- __init__.py
- config_flow.py
- coordinator.py
- sensor.py
- services.py
- manifest.json

Do not modify the domain name in manifest.json — it must be `gw_smart_charging`.