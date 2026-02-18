"""Smart Battery Charging Controller v3.2.0 for Home Assistant."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from .const import DOMAIN, VERSION
from .coordinator import SmartChargingCoordinator
from .views import async_setup_views

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "switch"]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# Old unique_id suffixes to remove from entity registry
_OLD_ENTITY_SUFFIXES = [
    # v3.0.x sensors
    "_activity_log", "_daily_statistics", "_prediction",
    "_statistics", "_soc_forecast", "_cost_optimization",
    "_battery_status",
    # v3.0.9 sensors
    "_forecast", "_schedule", "_charging_schedule",
    "_charging_plan", "_next_charging", "_tariff_info",
    "_consumption_forecast",
    # v3.2.0 broken sensors merged into attributes
    "_cost_today", "_cost_week", "_cost_month", "_hdo",
    # duplicated names from various versions
    "_price_forecast",
]


async def async_setup(hass, config):
    _LOGGER.info(f"Smart Battery Charging Controller v{VERSION}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = SmartChargingCoordinator(hass, entry.data, entry.entry_id)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    try:
        await coordinator.async_initialize()
    except Exception as e:
        _LOGGER.debug(f"Statistics load deferred: {e}")

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as e:
        _LOGGER.warning(f"Initial refresh failed (will retry): {e}")

    # Clean up old entities BEFORE setting up new platforms
    await _cleanup_old_entities(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _setup_services(hass, coordinator)

    try:
        await async_setup_views(hass)
    except Exception as e:
        _LOGGER.warning(f"Dashboard views setup failed: {e}")

    try:
        await _register_card(hass)
    except Exception:
        pass

    _LOGGER.info(f"v{VERSION} setup complete: 7 sensors, HDO={entry.data.get('hdo_sensor','sensor.egdtar')}")
    return True


async def _cleanup_old_entities(hass: HomeAssistant, entry: ConfigEntry):
    """Remove old/deprecated entities from previous versions."""
    registry = er.async_get(hass)
    removed = 0

    # Method 1: by unique_id suffix
    for suffix in _OLD_ENTITY_SUFFIXES:
        uid = f"{entry.entry_id}{suffix}"
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, uid)
        if entity_id:
            registry.async_remove(entity_id)
            removed += 1
            _LOGGER.info(f"Removed old entity: {entity_id}")

    # Method 2: by entity_id name pattern — catches orphans from all versions
    valid_suffixes = {"_battery_soc", "_battery_power", "_price", "_plan",
                      "_next", "_consumption", "_diag"}
    all_entries = er.async_entries_for_config_entry(registry, entry.entry_id)
    for ent in all_entries:
        if ent.domain != "sensor":
            continue
        uid = ent.unique_id or ""
        # Keep only current 7 sensors
        if not any(uid.endswith(s) for s in valid_suffixes):
            registry.async_remove(ent.entity_id)
            removed += 1
            _LOGGER.info(f"Removed orphan entity: {ent.entity_id} (uid={uid})")

    if removed:
        _LOGGER.info(f"Cleaned up {removed} old entities")


async def _register_card(hass):
    """Copy card JS to /config/www/ and register as Lovelace resource."""
    import os
    import shutil

    src = os.path.join(os.path.dirname(__file__), "ui", "smart-charging-card.js")
    if not os.path.exists(src):
        return

    # Step 1: Copy to /config/www/
    www_dir = hass.config.path("www")
    os.makedirs(www_dir, exist_ok=True)
    dst = os.path.join(www_dir, "smart-charging-card.js")
    try:
        if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
            shutil.copy2(src, dst)
            _LOGGER.info(f"Lovelace card copied to {dst}")
    except Exception as e:
        _LOGGER.warning(f"Could not copy card to www/: {e}")
        return

    # Step 2: Auto-register as Lovelace resource (storage mode dashboards)
    url = "/local/smart-charging-card.js"
    try:
        resources = hass.data.get("lovelace_resources")
        if resources is not None:
            items = resources.async_items()
            already = any(url in (r.get("url", "") or "") for r in items)
            if not already:
                await resources.async_create_item({"res_type": "module", "url": url})
                _LOGGER.info(f"Auto-registered Lovelace resource: {url}")
        else:
            _LOGGER.info(f"Lovelace card ready at {url} — add resource manually if using YAML mode")
    except Exception as e:
        _LOGGER.debug(f"Lovelace resource auto-register skipped: {e}")
        _LOGGER.info(f"Lovelace card ready at {url} — add manually: Resources → {url} (JavaScript module)")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    c = hass.data[DOMAIN].get(entry.entry_id)
    if c:
        try:
            await c.stats_tracker.async_save()
        except Exception:
            pass
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok


async def _setup_services(hass, coordinator):
    async def force_update(call):
        await coordinator.force_plan_update()

    async def get_schedule(call):
        p = coordinator.current_plan
        if not p:
            return {"error": "No plan"}
        return {
            "slots": [{"start": s.start_time.isoformat(), "end": s.end_time.isoformat(),
                        "target_soc": s.target_soc, "total_price": s.total_price,
                        "reason": s.reason, "priority": s.priority} for s in p.slots],
            "peaks": [{"time": pk.timestamp.isoformat(), "price": pk.price} for pk in p.predicted_peaks],
            "total_cost": p.total_cost, "total_kwh": p.total_kwh, "confidence": p.confidence,
        }

    hass.services.async_register(DOMAIN, "force_plan_update", force_update)
    hass.services.async_register(DOMAIN, "get_charging_schedule", get_schedule)
