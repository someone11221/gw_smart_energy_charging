"""Dashboard view for GW Smart Charging integration."""
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

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
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GW Smart Charging Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                        GW Smart Charging
                        <span class="version">v2.0.0</span>
                    </h1>
                    <p>Advanced battery charging optimization for Home Assistant</p>
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
                    <p>GW Smart Charging v2.0.0 | © 2024 | Created for Home Assistant</p>
                    <p style="margin-top: 10px;">For documentation and support, visit <a href="https://github.com/someone11221/gw_smart_energy_charging" style="color: white; text-decoration: underline;">GitHub Repository</a></p>
                </div>
            </div>
            
            <!-- NEW v1.9.5: JavaScript for controls and prediction timeline -->
            <script>
                // Toggle integration on/off
                async function toggleIntegration(activate) {{
                    const statusDiv = document.getElementById('control-status');
                    const entityId = 'switch.gw_smart_charging_auto_charging';
                    
                    try {{
                        const response = await fetch('/api/services/switch/' + (activate ? 'turn_on' : 'turn_off'), {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                entity_id: entityId
                            }})
                        }});
                        
                        if (response.ok) {{
                            statusDiv.style.display = 'block';
                            statusDiv.style.background = '#4CAF50';
                            statusDiv.style.color = 'white';
                            statusDiv.textContent = activate ? '✅ Integration activated successfully' : '🛑 Integration deactivated successfully';
                            setTimeout(() => {{ statusDiv.style.display = 'none'; }}, 5000);
                        }} else {{
                            throw new Error('Failed to toggle integration');
                        }}
                    }} catch (error) {{
                        statusDiv.style.display = 'block';
                        statusDiv.style.background = '#f44336';
                        statusDiv.style.color = 'white';
                        statusDiv.textContent = '❌ Error: ' + error.message;
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
                
                // Load and display prediction timeline
                async function loadPredictionTimeline() {{
                    const timeline = document.getElementById('prediction-timeline');
                    
                    try {{
                        const response = await fetch('/api/states/sensor.gw_smart_charging_schedule');
                        const data = await response.json();
                        
                        if (data && data.attributes && data.attributes.schedule) {{
                            const schedule = data.attributes.schedule;
                            let html = '';
                            
                            // Group by hours and show major actions
                            let lastMode = null;
                            let groupStart = null;
                            
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
                            timeline.innerHTML = '<p style="color: #666;">Schedule data not available</p>';
                        }}
                    }} catch (error) {{
                        timeline.innerHTML = '<p style="color: #f44336;">Error loading prediction: ' + error.message + '</p>';
                    }}
                }}
                
                // Load prediction on page load and refresh every 15 minutes
                loadPredictionTimeline();
                setInterval(loadPredictionTimeline, 15 * 60 * 1000); // Refresh every 15 minutes
            </script>
        </body>
        </html>
        """
        
        return html
