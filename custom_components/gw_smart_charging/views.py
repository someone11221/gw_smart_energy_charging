"""API views for Smart Battery Charging dashboard v3.2.0."""
import os, json, logging
from aiohttp import web
from datetime import datetime
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from .const import DOMAIN, VERSION

_LOGGER = logging.getLogger(__name__)


def _coord(hass):
    cs = list(hass.data.get(DOMAIN, {}).values())
    return cs[0] if cs else None


def _build(c) -> dict:
    d = c.data or {}
    bat = c.battery_controller._status
    plan = c.current_plan
    out = {
        "version": VERSION,
        "auto_enabled": c._auto_charging_enabled,
        "charging_active": c._charging_active,
        "fallback_active": getattr(c, '_fallback_active', False),
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "errors": d.get("errors", []),
        "debug_summary": d.get("debug_summary", {}),
        "battery": {},
        "current_price": d.get("current_price"),
        "price_forecast": d.get("price_forecast", {}),
        "consumption_forecast": d.get("consumption_forecast", {}),
        "consumption_hourly": d.get("consumption_hourly", []),
        "tariff_info": d.get("tariff_info", {}),
        "hdo": d.get("hdo", {}),
        "statistics": d.get("statistics", {}),
        "flat_price_compare": d.get("flat_price_compare", 4.5),
        "plan": {},
    }
    if bat:
        out["battery"] = {
            "soc": bat.soc, "power": bat.power, "capacity": bat.capacity,
            "charging": bat.charging, "discharging": bat.discharging,
        }
    if plan:
        try:
            out["plan"] = {
                "slots": [{"start": s.start_time.strftime("%Y-%m-%d %H:%M"),
                           "end": s.end_time.strftime("%Y-%m-%d %H:%M"),
                           "target_soc": s.target_soc,
                           "price": round(s.price, 6),
                           "total_price": round(s.total_price, 6),
                           "reason": s.reason, "priority": s.priority}
                          for s in plan.slots],
                "peaks": [{"time": p.timestamp.strftime("%Y-%m-%d %H:%M"),
                           "price": round(p.price, 6)} for p in plan.predicted_peaks],
                "total_cost": round(plan.total_cost, 2),
                "total_kwh": round(plan.total_kwh, 2),
                "confidence": round(plan.confidence, 3),
            }
        except Exception as e:
            out["errors"].append(str(e))
    return out


class DashboardView(HomeAssistantView):
    url = "/api/gw_smart_charging/dashboard"
    name = "api:gw_smart_charging:dashboard"
    requires_auth = False

    async def get(self, request):
        hass = request.app["hass"]
        path = os.path.join(os.path.dirname(__file__), "ui", "dashboard.html")
        try:
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            c = _coord(hass)
            data = _build(c) if c else {}
            html = html.replace("/*INITIAL_DATA_PLACEHOLDER*/",
                                f"const INITIAL_DATA = {json.dumps(data, default=str)};")
            return web.Response(text=html, content_type="text/html")
        except Exception as e:
            return web.Response(text=f"Error: {e}", status=500)


class DashboardDataView(HomeAssistantView):
    url = "/api/gw_smart_charging/data"
    name = "api:gw_smart_charging:data"
    requires_auth = False
    async def get(self, request):
        c = _coord(request.app["hass"])
        if not c: return web.json_response({"error": "Not loaded"}, status=503)
        return web.json_response(_build(c))


class StatisticsView(HomeAssistantView):
    url = "/api/gw_smart_charging/statistics"
    name = "api:gw_smart_charging:statistics"
    requires_auth = False
    async def get(self, request):
        c = _coord(request.app["hass"])
        if not c: return web.json_response({"error": "Not loaded"}, status=503)
        try:
            return web.json_response(c.stats_tracker.get_all_stats_for_dashboard())
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)


class DebugLogView(HomeAssistantView):
    """JSON debug events with optional filters."""
    url = "/api/gw_smart_charging/debug"
    name = "api:gw_smart_charging:debug"
    requires_auth = False
    async def get(self, request):
        c = _coord(request.app["hass"])
        if not c: return web.json_response({"error": "Not loaded"}, status=503)
        level = request.query.get("level")
        category = request.query.get("category")
        limit = int(request.query.get("limit", 200))
        events = c.dbg.get_events(level=level, category=category, limit=limit)
        return web.json_response({
            "summary": c.dbg.get_summary(),
            "events": events,
        })


class DebugDownloadView(HomeAssistantView):
    """Download full debug log as .txt or .json file."""
    url = "/api/gw_smart_charging/debug/download"
    name = "api:gw_smart_charging:debug:download"
    requires_auth = False
    async def get(self, request):
        c = _coord(request.app["hass"])
        if not c: return web.Response(text="Not loaded", status=503)
        fmt = request.query.get("format", "txt")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if fmt == "json":
            return web.Response(
                text=c.dbg.get_json(limit=500),
                content_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="gw_debug_{ts}.json"'})
        else:
            return web.Response(
                text=c.dbg.get_text(limit=500),
                content_type="text/plain; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="gw_debug_{ts}.txt"'})


class ToggleAutoView(HomeAssistantView):
    url = "/api/gw_smart_charging/auto/{state}"
    name = "api:gw_smart_charging:auto"
    requires_auth = False
    async def post(self, request, state):
        c = _coord(request.app["hass"])
        if not c: return web.json_response({"error": "No coordinator"}, status=503)
        await c.set_auto_charging(state == "on")
        return web.json_response({"ok": True})


class RefreshPlanView(HomeAssistantView):
    url = "/api/gw_smart_charging/refresh"
    name = "api:gw_smart_charging:refresh"
    requires_auth = False
    async def post(self, request):
        c = _coord(request.app["hass"])
        if not c: return web.json_response({"error": "No coordinator"}, status=503)
        await c.force_plan_update()
        return web.json_response({"ok": True})


class UpdateConfigView(HomeAssistantView):
    url = "/api/gw_smart_charging/config"
    name = "api:gw_smart_charging:config"
    requires_auth = False
    async def post(self, request):
        c = _coord(request.app["hass"])
        if not c: return web.json_response({"error": "No coordinator"}, status=503)
        try:
            body = await request.json()
            for k in ("home_consumption_kw", "battery_capacity", "charging_power",
                      "home_consumption_morning", "home_consumption_evening", "home_consumption_night"):
                if k in body:
                    v = float(body[k])
                    c.config[k] = v
                    if hasattr(c, 'strategy'):
                        c.strategy.config[k] = v
            c.dbg.info("config", f"Settings updated from dashboard: {body}")
            return web.json_response({"ok": True})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)


async def async_setup_views(hass: HomeAssistant):
    for v in (DashboardView, DashboardDataView, StatisticsView,
              DebugLogView, DebugDownloadView,
              ToggleAutoView, RefreshPlanView, UpdateConfigView):
        hass.http.register_view(v())
