"""Dashboard view for GW Smart Charging integration."""
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime
import json

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_LANGUAGE, DEFAULT_LANGUAGE
from .translations import get_translation, get_all_translations

_LOGGER = logging.getLogger(__name__)


class GWSmartChargingDashboardView(HomeAssistantView):
    """Provide a dashboard for GW Smart Charging integration."""

    url = f"/api/{DOMAIN}/dashboard"
    name = f"api:{DOMAIN}:dashboard"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the dashboard view."""
        self.hass = hass

    async def get(self, request):
        """Return the dashboard HTML."""
        
        # Get all integration data
        integration_data = self.hass.data.get(DOMAIN, {})
        
        # Build HTML dashboard
        html = self._build_dashboard_html(integration_data)
        
        return web.Response(
            text=html,
            content_type="text/html",
            charset="utf-8",
        )
    
    def _build_dashboard_html(self, integration_data: dict) -> str:
        """Build the dashboard HTML."""
        
        import json
        
        # Get language preference from first coordinator config
        language = DEFAULT_LANGUAGE
        for entry_id, coordinator in integration_data.items():
            if hasattr(coordinator, 'config'):
                language = coordinator.config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
                break
        
        # Get all translations for selected language
        t = get_all_translations(language)
        
        # Get entities from all coordinators
        entities_html = ""
        sensors_count = 0
        switches_count = 0
        
        for entry_id, coordinator in integration_data.items():
            if hasattr(coordinator, 'data'):
                data = coordinator.data or {}
                
                # Count entities
                entities_html += f"""
                <div class="integration-instance">
                    <h3>Integration Instance: {entry_id[:8]}...</h3>
                    <div class="status-badge">Status: {data.get('status', 'unknown')}</div>
                    <div class="last-update">Last Update: {data.get('last_update', 'never')}</div>
                </div>
                """
        
        # Get entity registry to count entities
        from homeassistant.helpers import entity_registry as er
        entity_reg = er.async_get(self.hass)
        
        for entity in entity_reg.entities.values():
            if entity.platform == DOMAIN:
                if entity.domain == "sensor":
                    sensors_count += 1
                elif entity.domain == "switch":
                    switches_count += 1
        
        # Get schedule data from sensor state
        schedule_data = []
        schedule_entity = self.hass.states.get('sensor.gw_smart_charging_schedule')
        if schedule_entity and schedule_entity.attributes:
            schedule_data = schedule_entity.attributes.get('schedule', [])
        
        # Get SOC forecast data for charts
        soc_forecast_data = []
        soc_entity = self.hass.states.get('sensor.gw_smart_charging_soc_forecast')
        if soc_entity and soc_entity.attributes:
            soc_forecast_data = soc_entity.attributes.get('soc_forecast', [])
        
        # Get forecast and price data for charts
        forecast_data = []
        price_data = []
        forecast_entity = self.hass.states.get('sensor.gw_smart_charging_forecast')
        if forecast_entity and forecast_entity.attributes:
            forecast_data = forecast_entity.attributes.get('forecast_15min', [])
            price_data = forecast_entity.attributes.get('price_15min', [])
        
        # Get switch state
        switch_state = "unknown"
        switch_entity = self.hass.states.get('switch.gw_smart_charging_auto_charging')
        if switch_entity:
            switch_state = switch_entity.state
        
        # Get diagnostics data for detailed display
        diagnostics_data = {}
        current_strategy = "Unknown"
        current_soc = "N/A"
        test_mode = "N/A"
        next_charge_time = "N/A"
        
        diagnostics_entity = self.hass.states.get('sensor.gw_smart_charging_diagnostics')
        if diagnostics_entity and diagnostics_entity.attributes:
            diagnostics_data = diagnostics_entity.attributes
            current_strategy = diagnostics_data.get('charging_strategy', 'Unknown')
            current_soc = diagnostics_data.get('current_soc_pct', 'N/A')
            test_mode = diagnostics_data.get('test_mode', False)
            
        # Get next charge information
        next_charge_entity = self.hass.states.get('sensor.gw_smart_charging_next_charge')
        if next_charge_entity:
            next_charge_time = next_charge_entity.state
        
        # Convert data to JSON for embedding
        schedule_json = json.dumps(schedule_data)
        soc_forecast_json = json.dumps(soc_forecast_data[:96] if len(soc_forecast_data) > 0 else [])
        price_json = json.dumps(price_data[:96] if len(price_data) > 0 else [])
        forecast_json = json.dumps(forecast_data[:96] if len(forecast_data) > 0 else [])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{t['dashboard_title']}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                
                .header {{
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                
                .header h1 {{
                    color: #333;
                    font-size: 32px;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }}
                
                .header .icon {{
                    font-size: 40px;
                }}
                
                .header .version {{
                    color: #666;
                    font-size: 14px;
                    font-weight: normal;
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                
                .stat-card {{
                    background: white;
                    border-radius: 12px;
                    padding: 25px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: transform 0.2s;
                }}
                
                .stat-card:hover {{
                    transform: translateY(-5px);
                }}
                
                .stat-card h3 {{
                    color: #666;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 10px;
                }}
                
                .stat-card .value {{
                    color: #333;
                    font-size: 36px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                
                .stat-card .label {{
                    color: #999;
                    font-size: 14px;
                }}
                
                .section {{
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                
                .section h2 {{
                    color: #333;
                    font-size: 24px;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                }}
                
                .entity-list {{
                    display: grid;
                    gap: 15px;
                }}
                
                .entity-item {{
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                }}
                
                .entity-item .entity-name {{
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 5px;
                }}
                
                .entity-item .entity-id {{
                    color: #666;
                    font-size: 14px;
                    font-family: 'Courier New', monospace;
                }}
                
                .status-badge {{
                    display: inline-block;
                    padding: 5px 15px;
                    background: #4CAF50;
                    color: white;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                
                .integration-instance {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 15px;
                }}
                
                .integration-instance h3 {{
                    color: #667eea;
                    margin-bottom: 10px;
                }}
                
                .last-update {{
                    color: #666;
                    font-size: 14px;
                    margin-top: 5px;
                }}
                
                .features-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 15px;
                    margin-top: 20px;
                }}
                
                .feature-item {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 10px;
                }}
                
                .feature-item .icon {{
                    color: #667eea;
                    font-size: 24px;
                }}
                
                .feature-item .text {{
                    color: #333;
                }}
                
                .footer {{
                    text-align: center;
                    color: white;
                    margin-top: 30px;
                    padding: 20px;
                    font-size: 14px;
                }}
                
                /* Control buttons NEW v1.9.5 */
                .controls-section {{
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                
                .control-buttons {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-top: 20px;
                }}
                
                .control-btn {{
                    padding: 15px 30px;
                    font-size: 16px;
                    font-weight: 600;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s;
                    text-decoration: none;
                    text-align: center;
                    display: inline-block;
                }}
                
                .control-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                }}
                
                .btn-primary {{
                    background: #4CAF50;
                    color: white;
                }}
                
                .btn-danger {{
                    background: #f44336;
                    color: white;
                }}
                
                .btn-warning {{
                    background: #ff9800;
                    color: white;
                }}
                
                .btn-info {{
                    background: #2196F3;
                    color: white;
                }}
                
                .prediction-timeline {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin-top: 20px;
                }}
                
                .timeline-item {{
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    padding: 10px;
                    border-left: 4px solid #667eea;
                    margin-bottom: 10px;
                    background: white;
                    border-radius: 4px;
                }}
                
                .timeline-time {{
                    font-weight: bold;
                    min-width: 100px;
                    color: #667eea;
                }}
                
                .timeline-action {{
                    flex: 1;
                }}
                
                .action-charge {{
                    color: #4CAF50;
                    font-weight: 600;
                }}
                
                .action-discharge {{
                    color: #f44336;
                    font-weight: 600;
                }}
                
                .action-solar {{
                    color: #ff9800;
                    font-weight: 600;
                }}
                
                .action-grid {{
                    color: #2196F3;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>
                        <span class="icon">🔋</span>
                        {t['dashboard_title']}
                        <span class="version">v2.3.0</span>
                    </h1>
                    <p>{t['integration_status']}: <strong style="color: #4CAF50;">{'Active' if switch_state == 'on' else 'Inactive'}</strong></p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Sensors</h3>
                        <div class="value">{sensors_count}</div>
                        <div class="label">Active Sensors</div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Switches</h3>
                        <div class="value">{switches_count}</div>
                        <div class="label">Control Switches</div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Update Interval</h3>
                        <div class="value">2</div>
                        <div class="label">Minutes</div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Resolution</h3>
                        <div class="value">15</div>
                        <div class="label">Minute Slots</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📊 Integration Status</h2>
                    {entities_html}
                </div>
                
                <div class="section">
                    <h2>✨ Features</h2>
                    <div class="features-grid">
                        <div class="feature-item">
                            <span class="icon">🤖</span>
                            <span class="text">Automatic charging control every 2 minutes</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">🎯</span>
                            <span class="text">15-minute interval optimization (96 slots/day)</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">🌞</span>
                            <span class="text">Intelligent self-consumption priority</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">💰</span>
                            <span class="text">Price threshold optimization with hysteresis</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">🔋</span>
                            <span class="text">SOC limits and battery protection</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">📊</span>
                            <span class="text">Advanced ML: weekday/weekend/holiday patterns</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">⚡</span>
                            <span class="text">Critical hours peak demand management</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">📈</span>
                            <span class="text">Real-time monitoring and diagnostics</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">🔄</span>
                            <span class="text">W to kWh unit conversion</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">📉</span>
                            <span class="text">Battery charge/discharge tracking</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">🎛️</span>
                            <span class="text">Nanogreen cheapest hours integration</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">🔌</span>
                            <span class="text">Additional switches with price control</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">🧪</span>
                            <span class="text">Advanced testing and debugging mode</span>
                        </div>
                        <div class="feature-item">
                            <span class="icon">🌍</span>
                            <span class="text">Czech holiday detection</span>
                        </div>
                    </div>
                </div>
                
                <!-- NEW v2.3.0: Charging Strategies Quick Reference -->
                <div class="section">
                    <h2>🎯 Charging Strategies Quick Reference</h2>
                    <p>Choose the strategy that best fits your energy tariff and usage pattern:</p>
                    
                    <div style="display: grid; gap: 15px; margin-top: 20px;">
                        <div style="padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white;">
                            <h3 style="margin: 0 0 10px 0;">🎨 Dynamic (Default)</h3>
                            <p style="margin: 5px 0; font-size: 14px;">
                                <strong>Best for:</strong> Most users, variable pricing<br>
                                <strong>How it works:</strong> Analyzes prices, forecasts, and ML patterns to find optimal charging times. Waits for lowest prices in trending markets.<br>
                                <strong>Pros:</strong> Maximum savings, intelligent optimization<br>
                                <strong>Cons:</strong> Less predictable charging times
                            </p>
                        </div>
                        
                        <div style="padding: 15px; background: #e3f2fd; border-left: 4px solid #2196F3; border-radius: 8px;">
                            <h3 style="margin: 0 0 10px 0; color: #1976D2;">⏰ 4/6 Lowest Hours</h3>
                            <p style="margin: 5px 0; font-size: 14px; color: #333;">
                                <strong>Best for:</strong> Predictable charging, medium batteries<br>
                                <strong>How it works:</strong> Always charges during 4 (or 6) cheapest hours in next 24h<br>
                                <strong>Pros:</strong> Simple, predictable, guaranteed charging<br>
                                <strong>Cons:</strong> May miss optimization opportunities
                            </p>
                        </div>
                        
                        <div style="padding: 15px; background: #f3e5f5; border-left: 4px solid #9c27b0; border-radius: 8px;">
                            <h3 style="margin: 0 0 10px 0; color: #7b1fa2;">🎛️ Nanogreen Only</h3>
                            <p style="margin: 5px 0; font-size: 14px; color: #333;">
                                <strong>Best for:</strong> Nanogreen users, trust external service<br>
                                <strong>How it works:</strong> Charges when Nanogreen sensor indicates cheapest hours<br>
                                <strong>Pros:</strong> Leverages external optimization<br>
                                <strong>Cons:</strong> Depends on Nanogreen availability
                            </p>
                        </div>
                        
                        <div style="padding: 15px; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 8px;">
                            <h3 style="margin: 0 0 10px 0; color: #f57c00;">💸 Price Threshold</h3>
                            <p style="margin: 5px 0; font-size: 14px; color: #333;">
                                <strong>Best for:</strong> Very cheap night tariffs, aggressive charging<br>
                                <strong>How it works:</strong> Charges whenever price drops below "Always Charge Price"<br>
                                <strong>Pros:</strong> Maximizes cheap electricity usage<br>
                                <strong>Cons:</strong> May overcharge if prices frequently low
                            </p>
                        </div>
                        
                        <div style="padding: 15px; background: #e8f5e9; border-left: 4px solid #4CAF50; border-radius: 8px;">
                            <h3 style="margin: 0 0 10px 0; color: #2e7d32;">🌞 Solar Priority</h3>
                            <p style="margin: 5px 0; font-size: 14px; color: #333;">
                                <strong>Best for:</strong> Maximizing self-consumption, sunny locations<br>
                                <strong>How it works:</strong> Prioritizes charging when solar forecast is high<br>
                                <strong>Pros:</strong> Minimal grid usage, green energy focus<br>
                                <strong>Cons:</strong> Weather dependent
                            </p>
                        </div>
                        
                        <div style="padding: 15px; background: #fce4ec; border-left: 4px solid #e91e63; border-radius: 8px;">
                            <h3 style="margin: 0 0 10px 0; color: #c2185b;">⚡ Peak Shaving</h3>
                            <p style="margin: 5px 0; font-size: 14px; color: #333;">
                                <strong>Best for:</strong> Demand charges, peak period tariffs<br>
                                <strong>How it works:</strong> Avoids grid during peak hours (uses critical hours setting)<br>
                                <strong>Pros:</strong> Reduces demand charges<br>
                                <strong>Cons:</strong> Requires proper critical hours configuration
                            </p>
                        </div>
                        
                        <div style="padding: 15px; background: #e0f2f1; border-left: 4px solid #009688; border-radius: 8px;">
                            <h3 style="margin: 0 0 10px 0; color: #00695c;">📊 TOU Optimized</h3>
                            <p style="margin: 5px 0; font-size: 14px; color: #333;">
                                <strong>Best for:</strong> Time-of-Use tariffs, multi-tier pricing<br>
                                <strong>How it works:</strong> Charges only in cheapest 40% of price range<br>
                                <strong>Pros:</strong> Perfect for TOU tariffs<br>
                                <strong>Cons:</strong> Requires clear price tiers
                            </p>
                        </div>
                        
                        <div style="padding: 15px; background: #fff9c4; border-left: 4px solid #fbc02d; border-radius: 8px;">
                            <h3 style="margin: 0 0 10px 0; color: #f57f17;">🤖 Adaptive Smart</h3>
                            <p style="margin: 5px 0; font-size: 14px; color: #333;">
                                <strong>Best for:</strong> Regular usage patterns, ML enthusiasts<br>
                                <strong>How it works:</strong> Learns from consumption and charges before high usage<br>
                                <strong>Pros:</strong> Self-optimizing, predictive<br>
                                <strong>Cons:</strong> Needs 30 days to learn patterns
                            </p>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #f0f7ff; border-left: 4px solid #2196F3; border-radius: 4px;">
                        <p style="margin: 0; color: #1976D2;">
                            <strong>💡 Recommendation:</strong> Start with "Dynamic" strategy. It works well for most scenarios. 
                            Use test mode to compare different strategies before committing to one.
                        </p>
                    </div>
                </div>
                
                <!-- NEW v2.3.0: Current Configuration Status -->
                <div class="section">
                    <h2>⚙️ Current Configuration</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>Charging Strategy</h3>
                            <div class="value" style="font-size: 18px;">{current_strategy}</div>
                            <div class="label">Active Strategy</div>
                        </div>
                        <div class="stat-card">
                            <h3>Current SOC</h3>
                            <div class="value">{current_soc}</div>
                            <div class="label">Battery State (%)</div>
                        </div>
                        <div class="stat-card">
                            <h3>Test Mode</h3>
                            <div class="value" style="font-size: 18px;">{'ON' if test_mode else 'OFF'}</div>
                            <div class="label">Debug Status</div>
                        </div>
                        <div class="stat-card">
                            <h3>Next Charge</h3>
                            <div class="value" style="font-size: 18px;">{next_charge_time}</div>
                            <div class="label">Scheduled</div>
                        </div>
                    </div>
                    <div style="margin-top: 20px; padding: 15px; background: #f0f7ff; border-left: 4px solid #2196F3; border-radius: 4px;">
                        <p style="margin: 0; color: #1976D2;">
                            <strong>💡 Hint:</strong> The charging strategy determines how the integration decides when to charge the battery. 
                            You can change it in Settings → Devices & Services → GW Smart Charging → Configure.
                        </p>
                    </div>
                </div>
                
                <!-- NEW v1.9.5: Control Panel -->
                <div class="controls-section">
                    <h2>🎛️ Control Panel</h2>
                    <p>Quick controls for the integration</p>
                    <div class="control-buttons">
                        <a href="/config/integrations/integration/gw_smart_charging" class="control-btn btn-info">
                            ⚙️ Configure Integration
                        </a>
                        <button class="control-btn btn-primary" onclick="toggleIntegration(true)">
                            ✅ Activate Integration
                        </button>
                        <button class="control-btn btn-danger" onclick="toggleIntegration(false)">
                            🛑 Deactivate Integration
                        </button>
                        <button class="control-btn btn-warning" onclick="toggleTestMode()">
                            🧪 Toggle Test Mode
                        </button>
                    </div>
                    <div id="control-status" style="margin-top: 15px; padding: 10px; border-radius: 5px; display: none;"></div>
                    
                    <!-- Test Mode Explanation -->
                    <div style="margin-top: 20px; padding: 15px; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 4px;">
                        <h3 style="margin: 0 0 10px 0; color: #f57c00;">🧪 Test Mode Information</h3>
                        <p style="margin: 5px 0; color: #555;">
                            <strong>What is Test Mode?</strong> When enabled, the integration calculates charging schedules but does NOT execute them. 
                            Scripts are not called, and the battery is not charged. This is useful for:
                        </p>
                        <ul style="margin: 10px 0; padding-left: 25px; color: #555;">
                            <li>Testing different configuration parameters without affecting the battery</li>
                            <li>Verifying charging logic before going live</li>
                            <li>Debugging issues with sensor data or schedules</li>
                            <li>Previewing how different strategies would behave</li>
                        </ul>
                        <p style="margin: 5px 0; color: #555;">
                            <strong>Current Status:</strong> Test mode is <strong style="color: {'#f57c00' if test_mode else '#4CAF50'};">{'ENABLED - Integration is in simulation mode' if test_mode else 'DISABLED - Integration is controlling the battery'}</strong>
                        </p>
                    </div>
                    
                    <!-- NEW v2.3.0: Testing Scenarios -->
                    <div style="margin-top: 20px; padding: 15px; background: #e8f5e9; border-left: 4px solid #4CAF50; border-radius: 4px;">
                        <h3 style="margin: 0 0 10px 0; color: #2e7d32;">🎯 Testing Scenarios</h3>
                        <p style="margin: 5px 0; color: #555;"><strong>Try these test scenarios to validate your configuration:</strong></p>
                        
                        <div style="margin-top: 15px;">
                            <details style="margin-bottom: 10px;">
                                <summary style="cursor: pointer; font-weight: bold; color: #2e7d32;">📊 Scenario 1: Price Threshold Testing</summary>
                                <div style="padding: 10px; margin-top: 5px; background: white; border-radius: 4px;">
                                    <p><strong>Goal:</strong> Verify charging activates at correct prices</p>
                                    <ol style="margin: 5px 0; padding-left: 20px;">
                                        <li>Enable test mode</li>
                                        <li>Set "Always Charge Price" to a specific value (e.g., 2.0 CZK/kWh)</li>
                                        <li>Check dashboard graphs to see when charging would trigger</li>
                                        <li>Verify it matches hours with price below your threshold</li>
                                    </ol>
                                </div>
                            </details>
                            
                            <details style="margin-bottom: 10px;">
                                <summary style="cursor: pointer; font-weight: bold; color: #2e7d32;">⚡ Scenario 2: Strategy Comparison</summary>
                                <div style="padding: 10px; margin-top: 5px; background: white; border-radius: 4px;">
                                    <p><strong>Goal:</strong> Compare different charging strategies</p>
                                    <ol style="margin: 5px 0; padding-left: 20px;">
                                        <li>Enable test mode</li>
                                        <li>Try "4 Lowest Hours" strategy, note the scheduled times</li>
                                        <li>Switch to "Dynamic" strategy, compare the schedule</li>
                                        <li>Check which provides better SOC forecast</li>
                                        <li>Choose the strategy that fits your needs</li>
                                    </ol>
                                </div>
                            </details>
                            
                            <details style="margin-bottom: 10px;">
                                <summary style="cursor: pointer; font-weight: bold; color: #2e7d32;">🔋 Scenario 3: Battery Limits Testing</summary>
                                <div style="padding: 10px; margin-top: 5px; background: white; border-radius: 4px;">
                                    <p><strong>Goal:</strong> Ensure SOC stays within limits</p>
                                    <ol style="margin: 5px 0; padding-left: 20px;">
                                        <li>Enable test mode</li>
                                        <li>Set Min SOC = 10%, Max SOC = 95%</li>
                                        <li>Check SOC forecast graph (orange line)</li>
                                        <li>Verify it never goes below 10% or above 95%</li>
                                        <li>Adjust target SOC if needed</li>
                                    </ol>
                                </div>
                            </details>
                            
                            <details style="margin-bottom: 10px;">
                                <summary style="cursor: pointer; font-weight: bold; color: #2e7d32;">🌅 Scenario 4: Critical Hours Validation</summary>
                                <div style="padding: 10px; margin-top: 5px; background: white; border-radius: 4px;">
                                    <p><strong>Goal:</strong> Verify higher SOC during peak hours</p>
                                    <ol style="margin: 5px 0; padding-left: 20px;">
                                        <li>Enable test mode</li>
                                        <li>Set Critical Hours: 17-21, Critical SOC: 80%</li>
                                        <li>Check SOC forecast for hours 17:00-21:00</li>
                                        <li>Verify SOC is maintained at 80% during this period</li>
                                        <li>Check that charging happens before if needed</li>
                                    </ol>
                                </div>
                            </details>
                        </div>
                        
                        <p style="margin-top: 15px; color: #555; font-size: 14px;">
                            <strong>💡 Tip:</strong> After testing, disable test mode to activate real battery control. Monitor the first 24 hours to ensure expected behavior.
                        </p>
                    </div>
                </div>
                
                <!-- NEW v2.2.0: Charts Section -->
                <div class="section">
                    <h2>📊 {t['price_chart']} & {t['24h_prediction']}</h2>
                    <div style="margin-bottom: 30px;">
                        <canvas id="priceChart" style="max-height: 300px;"></canvas>
                    </div>
                    <div style="margin-bottom: 30px;">
                        <canvas id="socChart" style="max-height: 300px;"></canvas>
                    </div>
                    <div style="margin-bottom: 30px;">
                        <canvas id="energyFlowChart" style="max-height: 300px;"></canvas>
                    </div>
                    
                    <!-- Debug info for data availability -->
                    <div style="margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                        <h3 style="margin: 0 0 10px 0; color: #666;">📊 Data Status</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                            <div>
                                <strong>Schedule Data:</strong> {len(schedule_data)} slots
                            </div>
                            <div>
                                <strong>SOC Forecast:</strong> {len(soc_forecast_data)} values
                            </div>
                            <div>
                                <strong>Price Data:</strong> {len(price_data)} values
                            </div>
                            <div>
                                <strong>Solar Forecast:</strong> {len(forecast_data)} values
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- NEW v1.9.5: 24h Prediction Plan -->
                <div class="section">
                    <h2>🔮 24-Hour Prediction Plan</h2>
                    <p>Next 24 hours charging/discharging plan (updated every 15 minutes)</p>
                    <div class="prediction-timeline" id="prediction-timeline">
                        <p style="color: #666;">Loading prediction data...</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🎨 Available Sensors</h2>
                    <div class="entity-list">
                        <div class="entity-item">
                            <div class="entity-name">Forecast Status</div>
                            <div class="entity-id">sensor.gw_smart_charging_forecast_status</div>
                        </div>
                        <div class="entity-item">
                            <div class="entity-name">Solar Forecast</div>
                            <div class="entity-id">sensor.gw_smart_charging_forecast</div>
                        </div>
                        <div class="entity-item">
                            <div class="entity-name">Electricity Price</div>
                            <div class="entity-id">sensor.gw_smart_charging_price</div>
                        </div>
                        <div class="entity-item">
                            <div class="entity-name">Charging Schedule</div>
                            <div class="entity-id">sensor.gw_smart_charging_schedule</div>
                        </div>
                        <div class="entity-item">
                            <div class="entity-name">SOC Forecast</div>
                            <div class="entity-id">sensor.gw_smart_charging_soc_forecast</div>
                        </div>
                        <div class="entity-item">
                            <div class="entity-name">Battery Power (Real-time)</div>
                            <div class="entity-id">sensor.gw_smart_charging_battery_power</div>
                        </div>
                        <div class="entity-item">
                            <div class="entity-name">Today's Battery Charge</div>
                            <div class="entity-id">sensor.gw_smart_charging_today_battery_charge</div>
                        </div>
                        <div class="entity-item">
                            <div class="entity-name">Today's Battery Discharge</div>
                            <div class="entity-id">sensor.gw_smart_charging_today_battery_discharge</div>
                        </div>
                        <div class="entity-item">
                            <div class="entity-name">Diagnostics</div>
                            <div class="entity-id">sensor.gw_smart_charging_diagnostics</div>
                        </div>
                        <div class="entity-item">
                            <div class="entity-name">Series Sensors (for charting)</div>
                            <div class="entity-id">sensor.gw_smart_charging_series_* (pv, load, battery_charge, battery_discharge, grid_import, soc_forecast)</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🔧 Configuration</h2>
                    <p>Configure the integration through <strong>Settings → Devices & Services → GW Smart Charging</strong></p>
                    <p style="margin-top: 10px;">All sensors support W to kWh conversion for proper logic operation.</p>
                    <p style="margin-top: 10px;">Battery power sensor: <strong>positive values = discharging</strong>, <strong>negative values = charging</strong></p>
                </div>
                
                <div class="footer">
                    <p>Smart Battery Charging Controller v2.3.0 | © 2024 Martin Rak | Created for Home Assistant</p>
                    <p style="margin-top: 10px;">For documentation and support, visit <a href="https://github.com/someone11221/gw_smart_energy_charging" style="color: white; text-decoration: underline;">GitHub Repository</a></p>
                </div>
            </div>
            
            <!-- NEW v1.9.5: JavaScript for controls and prediction timeline -->
            <script>
                // Embedded schedule data from backend (fixes JSON parsing error)
                const SCHEDULE_DATA = {schedule_json};
                const SOC_FORECAST_DATA = {soc_forecast_json};
                const PRICE_DATA = {price_json};
                const FORECAST_DATA = {forecast_json};
                const SWITCH_STATE = '{switch_state}';
                const CURRENT_LANGUAGE = "{language}";
                
                // Debug logging
                console.log('Dashboard Data Loaded:', {{
                    scheduleSlots: SCHEDULE_DATA.length,
                    socForecastValues: SOC_FORECAST_DATA.length,
                    priceValues: PRICE_DATA.length,
                    forecastValues: FORECAST_DATA.length,
                    switchState: SWITCH_STATE,
                    language: CURRENT_LANGUAGE
                }});
                
                // Initialize charts on page load
                window.addEventListener('DOMContentLoaded', function() {{
                    console.log('Initializing charts...');
                    initializeCharts();
                    loadPredictionTimeline();
                }});
                
                // Initialize all charts
                function initializeCharts() {{
                    initPriceChart();
                    initSocChart();
                    initEnergyFlowChart();
                }}
                
                // Price chart with charging schedule overlay
                function initPriceChart() {{
                    const ctx = document.getElementById('priceChart');
                    if (!ctx) return;
                    
                    // Generate labels for 96 15-minute intervals (24 hours)
                    const labels = [];
                    for (let h = 0; h < 24; h++) {{
                        for (let m = 0; m < 60; m += 15) {{
                            labels.push(`${{h.toString().padStart(2, '0')}}:${{m.toString().padStart(2, '0')}}`);
                        }}
                    }}
                    
                    // Prepare charging schedule overlay
                    const chargingData = new Array(96).fill(null);
                    if (SCHEDULE_DATA && SCHEDULE_DATA.length > 0) {{
                        SCHEDULE_DATA.forEach((slot, idx) => {{
                            if (slot.should_charge && idx < 96) {{
                                chargingData[idx] = PRICE_DATA[idx] || 0;
                            }}
                        }});
                    }}
                    
                    new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: labels,
                            datasets: [
                                {{
                                    label: CURRENT_LANGUAGE === 'cs' ? 'Cena elektřiny (CZK/kWh)' : 'Electricity Price (CZK/kWh)',
                                    data: PRICE_DATA.length > 0 ? PRICE_DATA.slice(0, 96) : [],
                                    borderColor: 'rgb(102, 126, 234)',
                                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                    tension: 0.3,
                                    fill: true
                                }},
                                {{
                                    label: CURRENT_LANGUAGE === 'cs' ? 'Plánované nabíjení' : 'Planned Charging',
                                    data: chargingData,
                                    borderColor: 'rgb(76, 175, 80)',
                                    backgroundColor: 'rgba(76, 175, 80, 0.3)',
                                    borderWidth: 3,
                                    pointRadius: 4,
                                    pointHoverRadius: 6
                                }}
                            ]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: true,
                            interaction: {{
                                mode: 'index',
                                intersect: false
                            }},
                            scales: {{
                                x: {{
                                    display: true,
                                    ticks: {{
                                        maxTicksLimit: 24,
                                        callback: function(value, index) {{
                                            return index % 4 === 0 ? labels[index] : '';
                                        }}
                                    }}
                                }},
                                y: {{
                                    display: true,
                                    title: {{
                                        display: true,
                                        text: 'CZK/kWh'
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}
                
                // SOC forecast chart
                function initSocChart() {{
                    const ctx = document.getElementById('socChart');
                    if (!ctx) {{
                        console.error('SOC chart canvas not found');
                        return;
                    }}
                    
                    console.log('Initializing SOC chart with data:', SOC_FORECAST_DATA);
                    
                    const labels = [];
                    for (let h = 0; h < 24; h++) {{
                        for (let m = 0; m < 60; m += 15) {{
                            labels.push(`${{h.toString().padStart(2, '0')}}:${{m.toString().padStart(2, '0')}}`);
                        }}
                    }}
                    
                    // Ensure we have valid data or use placeholder
                    const socData = SOC_FORECAST_DATA && SOC_FORECAST_DATA.length > 0 
                        ? SOC_FORECAST_DATA.slice(0, 96) 
                        : new Array(96).fill(null);
                    
                    console.log('SOC chart data points:', socData.length, 'First few values:', socData.slice(0, 5));
                    
                    new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: labels,
                            datasets: [{{
                                label: CURRENT_LANGUAGE === 'cs' ? 'Předpověď stavu baterie (%)' : 'Battery SOC Forecast (%)',
                                data: socData,
                                borderColor: 'rgb(255, 159, 64)',
                                backgroundColor: 'rgba(255, 159, 64, 0.1)',
                                tension: 0.3,
                                fill: true,
                                spanGaps: true  // Draw line even if there are null values
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: true,
                            scales: {{
                                x: {{
                                    display: true,
                                    ticks: {{
                                        maxTicksLimit: 24,
                                        callback: function(value, index) {{
                                            return index % 4 === 0 ? labels[index] : '';
                                        }}
                                    }}
                                }},
                                y: {{
                                    display: true,
                                    min: 0,
                                    max: 100,
                                    title: {{
                                        display: true,
                                        text: '%'
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}
                
                // Energy flow chart
                function initEnergyFlowChart() {{
                    const ctx = document.getElementById('energyFlowChart');
                    if (!ctx) return;
                    
                    const labels = [];
                    for (let h = 0; h < 24; h++) {{
                        for (let m = 0; m < 60; m += 15) {{
                            labels.push(`${{h.toString().padStart(2, '0')}}:${{m.toString().padStart(2, '0')}}`);
                        }}
                    }}
                    
                    new Chart(ctx, {{
                        type: 'bar',
                        data: {{
                            labels: labels,
                            datasets: [{{
                                label: CURRENT_LANGUAGE === 'cs' ? 'Solární výroba (kWh)' : 'Solar Production (kWh)',
                                data: FORECAST_DATA.length > 0 ? FORECAST_DATA.slice(0, 96) : [],
                                backgroundColor: 'rgba(255, 206, 86, 0.7)',
                                borderColor: 'rgb(255, 206, 86)',
                                borderWidth: 1
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: true,
                            scales: {{
                                x: {{
                                    display: true,
                                    ticks: {{
                                        maxTicksLimit: 24,
                                        callback: function(value, index) {{
                                            return index % 4 === 0 ? labels[index] : '';
                                        }}
                                    }}
                                }},
                                y: {{
                                    display: true,
                                    title: {{
                                        display: true,
                                        text: 'kWh'
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}
                
                // Get authentication token from Home Assistant
                function getAuthToken() {{
                    // Try to get token from localStorage (Home Assistant stores it there)
                    return localStorage.getItem('hassTokens') ? 
                           JSON.parse(localStorage.getItem('hassTokens')).access_token : null;
                }}
                
                // Toggle integration on/off
                async function toggleIntegration(activate) {{
                    const statusDiv = document.getElementById('control-status');
                    const entityId = 'switch.gw_smart_charging_auto_charging';
                    
                    try {{
                        const token = getAuthToken();
                        const headers = {{
                            'Content-Type': 'application/json',
                        }};
                        
                        // Add authorization header if token is available
                        if (token) {{
                            headers['Authorization'] = `Bearer ${{token}}`;
                        }}
                        
                        const response = await fetch('/api/services/switch/' + (activate ? 'turn_on' : 'turn_off'), {{
                            method: 'POST',
                            headers: headers,
                            body: JSON.stringify({{
                                entity_id: entityId
                            }})
                        }});
                        
                        if (response.ok) {{
                            statusDiv.style.display = 'block';
                            statusDiv.style.background = '#4CAF50';
                            statusDiv.style.color = 'white';
                            statusDiv.textContent = activate ? '✅ Integration activated successfully' : '🛑 Integration deactivated successfully';
                            setTimeout(() => {{ 
                                statusDiv.style.display = 'none';
                                // Reload page to show updated state
                                window.location.reload();
                            }}, 2000);
                        }} else {{
                            const errorText = await response.text();
                            throw new Error(`Failed to toggle integration: ${{response.status}} - ${{errorText}}`);
                        }}
                    }} catch (error) {{
                        statusDiv.style.display = 'block';
                        statusDiv.style.background = '#f44336';
                        statusDiv.style.color = 'white';
                        statusDiv.textContent = '❌ Error: ' + error.message;
                        console.error('Toggle error:', error);
                    }}
                }}
                
                // Toggle test mode
                async function toggleTestMode() {{
                    const statusDiv = document.getElementById('control-status');
                    statusDiv.style.display = 'block';
                    statusDiv.style.background = '#ff9800';
                    statusDiv.style.color = 'white';
                    statusDiv.textContent = '🧪 Test mode feature coming soon - configure via integration settings';
                    setTimeout(() => {{ statusDiv.style.display = 'none'; }}, 5000);
                }}
                
                // Load and display prediction timeline using embedded data
                function loadPredictionTimeline() {{
                    const timeline = document.getElementById('prediction-timeline');
                    
                    try {{
                        const schedule = SCHEDULE_DATA;
                        
                        if (schedule && schedule.length > 0) {{
                            let html = '';
                            
                            // Group by hours and show major actions
                            let lastMode = null;
                            
                            schedule.forEach((slot, idx) => {{
                                const mode = slot.mode || 'idle';
                                const time = slot.time || '';
                                const soc = slot.soc_pct_end || 0;
                                const price = slot.price_czk_kwh || 0;
                                
                                // Only show significant mode changes
                                if (mode !== lastMode && mode !== 'idle' && mode !== 'self_consume') {{
                                    let actionClass = 'action-grid';
                                    let actionText = '';
                                    
                                    if (mode.includes('charge')) {{
                                        actionClass = 'action-charge';
                                        actionText = mode.includes('solar') ? '🌞 Charge from Solar' : '⚡ Charge from Grid';
                                    }} else if (mode.includes('discharge')) {{
                                        actionClass = 'action-discharge';
                                        actionText = '🔋 Discharge Battery';
                                    }}
                                    
                                    html += `
                                        <div class="timeline-item">
                                            <div class="timeline-time">${{time}}</div>
                                            <div class="timeline-action ${{actionClass}}">${{actionText}}</div>
                                            <div style="min-width: 100px;">SOC: ${{soc.toFixed(1)}}%</div>
                                            <div style="min-width: 100px;">Price: ${{price.toFixed(2)}} CZK</div>
                                        </div>
                                    `;
                                    lastMode = mode;
                                }}
                            }});
                            
                            if (html) {{
                                timeline.innerHTML = html;
                            }} else {{
                                timeline.innerHTML = '<p style="color: #666;">No significant charging/discharging actions planned for next 24h</p>';
                            }}
                        }} else {{
                            timeline.innerHTML = '<p style="color: #666;">Schedule data not available yet. Integration may still be initializing.</p>';
                        }}
                    }} catch (error) {{
                        timeline.innerHTML = '<p style="color: #f44336;">Error loading prediction: ' + error.message + '</p>';
                        console.error('Prediction error:', error);
                    }}
                }}
                
                // Update button states based on current switch state
                function updateButtonStates() {{
                    const activateBtn = document.querySelector('.btn-primary');
                    const deactivateBtn = document.querySelector('.btn-danger');
                    
                    if (SWITCH_STATE === 'on') {{
                        if (activateBtn) {{
                            activateBtn.style.opacity = '0.5';
                            activateBtn.style.cursor = 'not-allowed';
                        }}
                        if (deactivateBtn) {{
                            deactivateBtn.style.opacity = '1';
                            deactivateBtn.style.cursor = 'pointer';
                        }}
                    }} else if (SWITCH_STATE === 'off') {{
                        if (activateBtn) {{
                            activateBtn.style.opacity = '1';
                            activateBtn.style.cursor = 'pointer';
                        }}
                        if (deactivateBtn) {{
                            deactivateBtn.style.opacity = '0.5';
                            deactivateBtn.style.cursor = 'not-allowed';
                        }}
                    }}
                }}
                
                // Load prediction on page load
                document.addEventListener('DOMContentLoaded', function() {{
                    loadPredictionTimeline();
                    updateButtonStates();
                }});
                
                // Also call immediately in case DOMContentLoaded already fired
                loadPredictionTimeline();
                updateButtonStates();
            </script>
        </body>
        </html>
        """
        
        return html
