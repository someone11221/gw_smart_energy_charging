/**
 * GW Smart Charging Card
 * Custom Lovelace card for GW Smart Charging integration
 * Version: 2.1.0 - Enhanced dashboard, improved charging logic, multi-language support
 */

class GWSmartChargingCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity (e.g., sensor.gw_smart_charging_diagnostics)');
    }
    this._config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  render() {
    if (!this._hass || !this._config.entity) {
      return;
    }

    const entity = this._hass.states[this._config.entity];
    if (!entity) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="card-content">Entity ${this._config.entity} not found</div>
        </ha-card>
      `;
      return;
    }

    // Get all related entities
    const forecastEntity = this._hass.states['sensor.gw_smart_charging_forecast'];
    const scheduleEntity = this._hass.states['sensor.gw_smart_charging_schedule'];
    const socEntity = this._hass.states['sensor.gw_smart_charging_soc_forecast'];
    const batteryPowerEntity = this._hass.states['sensor.gw_smart_charging_battery_power'];
    const dailyStatsEntity = this._hass.states['sensor.gw_smart_charging_daily_statistics'];
    const switchEntity = this._hass.states['switch.gw_smart_charging_auto_charging'];

    const batteryMetrics = entity.attributes.battery_power_w !== undefined ? entity.attributes : {};
    const currentSoc = batteryPowerEntity?.attributes?.current_soc_pct || entity.attributes.battery_soc_pct || 0;
    const batteryStatus = batteryPowerEntity?.attributes?.status || entity.attributes.battery_status || 'unknown';
    const currentMode = entity.attributes.current_mode || 'unknown';
    const shouldCharge = entity.attributes.should_charge_now || false;

    const peakForecast = forecastEntity?.state || 0;
    const currentPrice = forecastEntity?.attributes?.current_price_czk_kwh || 0;
    const nextChargeTime = scheduleEntity?.attributes?.next_charge_time || 'none';
    const plannedGridCharge = dailyStatsEntity?.attributes?.planned_grid_charge_kwh || 0;

    this.shadowRoot.innerHTML = `
      <style>
        ha-card {
          padding: 16px;
        }
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .card-title {
          font-size: 24px;
          font-weight: 500;
        }
        .status-badge {
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
          text-transform: uppercase;
        }
        .status-active {
          background: #4caf50;
          color: white;
        }
        .status-idle {
          background: #9e9e9e;
          color: white;
        }
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 12px;
          margin-bottom: 16px;
        }
        .metric-card {
          background: var(--primary-background-color);
          padding: 12px;
          border-radius: 8px;
          border: 1px solid var(--divider-color);
        }
        .metric-label {
          font-size: 12px;
          color: var(--secondary-text-color);
          margin-bottom: 4px;
        }
        .metric-value {
          font-size: 20px;
          font-weight: 500;
        }
        .metric-unit {
          font-size: 14px;
          color: var(--secondary-text-color);
          margin-left: 4px;
        }
        .soc-container {
          margin-bottom: 16px;
        }
        .soc-bar-wrapper {
          background: var(--primary-background-color);
          border-radius: 8px;
          padding: 8px;
          border: 1px solid var(--divider-color);
        }
        .soc-bar {
          height: 24px;
          background: linear-gradient(90deg, #ff5722 0%, #ffc107 50%, #4caf50 100%);
          border-radius: 4px;
          position: relative;
          overflow: hidden;
        }
        .soc-fill {
          height: 100%;
          background: rgba(255, 255, 255, 0.3);
          border-radius: 4px;
          transition: width 0.3s ease;
        }
        .soc-text {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-weight: 500;
          color: white;
          text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        .info-section {
          background: var(--primary-background-color);
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 12px;
          border: 1px solid var(--divider-color);
        }
        .info-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid var(--divider-color);
        }
        .info-row:last-child {
          border-bottom: none;
        }
        .info-label {
          color: var(--secondary-text-color);
        }
        .info-value {
          font-weight: 500;
        }
        .mode-indicator {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
          text-transform: uppercase;
        }
        .mode-grid_charge {
          background: #2196f3;
          color: white;
        }
        .mode-solar_charge {
          background: #ffc107;
          color: black;
        }
        .mode-battery_discharge {
          background: #ff5722;
          color: white;
        }
        .mode-self_consume {
          background: #4caf50;
          color: white;
        }
        .switch-container {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: var(--primary-background-color);
          padding: 12px;
          border-radius: 8px;
          border: 1px solid var(--divider-color);
        }
        .switch-label {
          font-weight: 500;
        }
        
        /* NEW v1.9.5: Prediction Timeline */
        .prediction-section {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid var(--divider-color);
        }
        .prediction-title {
          font-size: 14px;
          font-weight: 600;
          margin-bottom: 12px;
          color: var(--primary-text-color);
        }
        .timeline-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px;
          margin-bottom: 6px;
          background: var(--secondary-background-color);
          border-radius: 6px;
          border-left: 3px solid var(--divider-color);
        }
        .timeline-time {
          font-weight: 600;
          min-width: 60px;
          font-size: 13px;
        }
        .timeline-action {
          flex: 1;
          font-size: 13px;
        }
        .timeline-soc {
          font-size: 12px;
          color: var(--secondary-text-color);
        }
        .action-charge {
          color: #4caf50;
          font-weight: 600;
        }
        .action-solar {
          color: #ff9800;
          font-weight: 600;
        }
        .action-discharge {
          color: #f44336;
          font-weight: 600;
        }
      </style>

      <ha-card>
        <div class="card-header">
          <div class="card-title">⚡ GW Smart Charging</div>
          <div class="status-badge status-${batteryStatus}">
            ${batteryStatus}
          </div>
        </div>

        <div class="soc-container">
          <div class="metric-label">Battery State of Charge</div>
          <div class="soc-bar-wrapper">
            <div class="soc-bar">
              <div class="soc-fill" style="width: ${100 - currentSoc}%"></div>
              <div class="soc-text">${currentSoc.toFixed(1)}%</div>
            </div>
          </div>
        </div>

        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-label">Solar Forecast Peak</div>
            <div class="metric-value">
              ${parseFloat(peakForecast).toFixed(2)}
              <span class="metric-unit">kW</span>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Current Price</div>
            <div class="metric-value">
              ${parseFloat(currentPrice).toFixed(2)}
              <span class="metric-unit">CZK/kWh</span>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Planned Grid Charge</div>
            <div class="metric-value">
              ${parseFloat(plannedGridCharge).toFixed(2)}
              <span class="metric-unit">kWh</span>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Next Charge</div>
            <div class="metric-value" style="font-size: 16px;">
              ${nextChargeTime}
            </div>
          </div>
        </div>

        <div class="info-section">
          <div class="info-row">
            <span class="info-label">Current Mode</span>
            <span class="info-value">
              <span class="mode-indicator mode-${currentMode.replace(/_/g, '-')}">
                ${currentMode.replace(/_/g, ' ')}
              </span>
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">Should Charge Now</span>
            <span class="info-value">${shouldCharge ? 'Yes ✓' : 'No ✗'}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Last Update</span>
            <span class="info-value">${entity.attributes.last_update || 'never'}</span>
          </div>
        </div>

        ${switchEntity ? `
          <div class="switch-container">
            <span class="switch-label">Automatic Charging</span>
            <ha-switch
              .checked=${switchEntity.state === 'on'}
              @change=${(e) => this._toggleSwitch(e, switchEntity.entity_id)}
            ></ha-switch>
          </div>
        ` : ''}
        
        ${this._renderPredictionTimeline(scheduleEntity)}
      </ha-card>
    `;
  }

  _renderPredictionTimeline(scheduleEntity) {
    if (!scheduleEntity || !scheduleEntity.attributes || !scheduleEntity.attributes.schedule) {
      return `
        <div class="prediction-section">
          <div class="prediction-title">📅 24h Prediction</div>
          <div style="color: var(--secondary-text-color); font-size: 13px;">No schedule data available</div>
        </div>
      `;
    }

    const schedule = scheduleEntity.attributes.schedule;
    let timelineHtml = '';
    let lastMode = null;
    let significantEvents = 0;
    
    // Extract significant events (mode changes, only show first 8)
    schedule.forEach((slot, idx) => {
      if (significantEvents >= 8) return;
      
      const mode = slot.mode || 'idle';
      const time = slot.time || '';
      const soc = slot.soc_pct_end || 0;
      
      // Only show significant mode changes
      if (mode !== lastMode && mode !== 'idle' && mode !== 'self_consume') {
        let actionClass = '';
        let actionIcon = '';
        let actionText = '';
        
        if (mode.includes('solar_charge')) {
          actionClass = 'action-solar';
          actionIcon = '🌞';
          actionText = 'Solar Charging';
        } else if (mode.includes('grid_charge')) {
          actionClass = 'action-charge';
          actionIcon = '⚡';
          actionText = 'Grid Charging';
        } else if (mode.includes('discharge')) {
          actionClass = 'action-discharge';
          actionIcon = '🔋';
          actionText = 'Battery Discharge';
        }
        
        if (actionText) {
          timelineHtml += `
            <div class="timeline-item">
              <div class="timeline-time">${time}</div>
              <div class="timeline-action ${actionClass}">${actionIcon} ${actionText}</div>
              <div class="timeline-soc">→ ${soc.toFixed(0)}%</div>
            </div>
          `;
          significantEvents++;
        }
        lastMode = mode;
      }
    });
    
    if (!timelineHtml) {
      timelineHtml = '<div style="color: var(--secondary-text-color); font-size: 13px;">No significant actions planned</div>';
    }
    
    return `
      <div class="prediction-section">
        <div class="prediction-title">📅 Next 24h Plan (updates every 15min)</div>
        ${timelineHtml}
      </div>
    `;
  }

  _toggleSwitch(e, entityId) {
    const checked = e.target.checked;
    this._hass.callService('switch', checked ? 'turn_on' : 'turn_off', {
      entity_id: entityId
    });
  }

  getCardSize() {
    return 6;
  }
}

customElements.define('gw-smart-charging-card', GWSmartChargingCard);

// Register the card
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'gw-smart-charging-card',
  name: 'GW Smart Charging Card',
  description: 'Custom card for GW Smart Charging integration',
  preview: true,
});

console.info(
  '%c  GW-SMART-CHARGING-CARD  %c Version 2.1.0 ',
  'color: white; background: #764ba2; font-weight: 700;',
  'color: #764ba2; background: white; font-weight: 700;'
);
