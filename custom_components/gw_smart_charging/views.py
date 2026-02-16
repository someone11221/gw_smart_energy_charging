"""API views for Smart Battery Charging Controller dashboard."""
import os
import logging
from aiohttp import web
from datetime import datetime

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class DashboardView(HomeAssistantView):
    """View to serve the dashboard HTML."""
    
    url = "/api/gw_smart_charging/dashboard"
    name = "api:gw_smart_charging:dashboard"
    requires_auth = False
    
    async def get(self, request):
        """Serve dashboard HTML."""
        dashboard_path = os.path.join(
            os.path.dirname(__file__),
            "ui",
            "dashboard.html"
        )
        
        try:
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            return web.Response(text=html, content_type='text/html')
        except Exception as e:
            _LOGGER.error(f"Error serving dashboard: {e}")
            return web.Response(text=f"Error: {e}", status=500)


class DashboardDataView(HomeAssistantView):
    """View to provide dashboard data."""
    
    url = "/api/gw_smart_charging/data"
    name = "api:gw_smart_charging:data"
    requires_auth = False
    
    async def get(self, request):
        """Get current dashboard data."""
        hass: HomeAssistant = request.app["hass"]
        
        try:
            # Get the first coordinator (assuming single instance)
            coordinators = list(hass.data.get(DOMAIN, {}).values())
            if not coordinators:
                return web.json_response({"error": "No coordinator found"}, status=404)
            
            coordinator = coordinators[0]
            
            # Build response data
            data = {}
            
            # Battery status
            if coordinator.battery_controller._status:
                status = coordinator.battery_controller._status
                data["battery_status"] = {
                    "soc": status.soc,
                    "power": status.power,
                    "capacity": status.capacity,
                    "charging": status.charging,
                    "discharging": status.discharging,
                }
            
            # Current price
            current_price = await coordinator.price_provider.get_current_price()
            data["current_price"] = current_price
            
            # Price forecast
            forecast = await coordinator.price_provider.get_forecast(24)
            if forecast:
                data["price_forecast"] = {
                    "prices": [
                        {
                            "time": p.timestamp.isoformat(),
                            "price": p.price
                        }
                        for p in forecast.prices
                    ],
                    "min_price": forecast.min_price,
                    "max_price": forecast.max_price,
                    "avg_price": forecast.avg_price,
                }
            
            # Charging plan
            if coordinator.current_plan:
                plan = coordinator.current_plan
                data["charging_plan"] = {
                    "slots": [
                        {
                            "start": slot.start_time.isoformat(),
                            "end": slot.end_time.isoformat(),
                            "target_soc": slot.target_soc,
                            "price": slot.price,
                            "reason": slot.reason,
                            "priority": slot.priority,
                        }
                        for slot in plan.slots
                    ],
                    "predicted_peaks": [
                        {
                            "time": peak.timestamp.isoformat(),
                            "price": peak.price,
                        }
                        for peak in plan.predicted_peaks
                    ],
                    "total_cost": plan.total_cost,
                    "total_kwh": plan.total_kwh,
                    "confidence": plan.confidence,
                }
            
            # Status
            data["charging_active"] = coordinator._charging_active
            data["auto_enabled"] = coordinator._auto_charging_enabled
            data["last_update"] = datetime.now().isoformat()
            
            return web.json_response(data)
            
        except Exception as e:
            _LOGGER.error(f"Error getting dashboard data: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)


class EnableAutoChargingView(HomeAssistantView):
    """View to enable auto charging."""
    
    url = "/api/gw_smart_charging/enable_auto"
    name = "api:gw_smart_charging:enable_auto"
    requires_auth = False
    
    async def post(self, request):
        """Enable auto charging."""
        hass: HomeAssistant = request.app["hass"]
        
        try:
            coordinators = list(hass.data.get(DOMAIN, {}).values())
            if not coordinators:
                return web.json_response({"error": "No coordinator found"}, status=404)
            
            coordinator = coordinators[0]
            await coordinator.set_auto_charging(True)
            
            return web.json_response({"status": "enabled"})
            
        except Exception as e:
            _LOGGER.error(f"Error enabling auto charging: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)


class DisableAutoChargingView(HomeAssistantView):
    """View to disable auto charging."""
    
    url = "/api/gw_smart_charging/disable_auto"
    name = "api:gw_smart_charging:disable_auto"
    requires_auth = False
    
    async def post(self, request):
        """Disable auto charging."""
        hass: HomeAssistant = request.app["hass"]
        
        try:
            coordinators = list(hass.data.get(DOMAIN, {}).values())
            if not coordinators:
                return web.json_response({"error": "No coordinator found"}, status=404)
            
            coordinator = coordinators[0]
            await coordinator.set_auto_charging(False)
            
            return web.json_response({"status": "disabled"})
            
        except Exception as e:
            _LOGGER.error(f"Error disabling auto charging: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)


class RefreshPlanView(HomeAssistantView):
    """View to force plan refresh."""
    
    url = "/api/gw_smart_charging/refresh_plan"
    name = "api:gw_smart_charging:refresh_plan"
    requires_auth = False
    
    async def post(self, request):
        """Force plan refresh."""
        hass: HomeAssistant = request.app["hass"]
        
        try:
            coordinators = list(hass.data.get(DOMAIN, {}).values())
            if not coordinators:
                return web.json_response({"error": "No coordinator found"}, status=404)
            
            coordinator = coordinators[0]
            await coordinator.force_plan_update()
            
            return web.json_response({"status": "refreshed"})
            
        except Exception as e:
            _LOGGER.error(f"Error refreshing plan: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)


async def async_setup_views(hass: HomeAssistant):
    """Register dashboard views."""
    hass.http.register_view(DashboardView())
    hass.http.register_view(DashboardDataView())
    hass.http.register_view(EnableAutoChargingView())
    hass.http.register_view(DisableAutoChargingView())
    hass.http.register_view(RefreshPlanView())
    
    _LOGGER.info("Dashboard views registered")
