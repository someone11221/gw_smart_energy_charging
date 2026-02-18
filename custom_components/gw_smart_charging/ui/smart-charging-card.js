/**
 * Smart Battery Charging – Lovelace Card v3.2.0
 * 
 * Installation: Copy to www/ folder, add as resource:
 *   /local/smart-charging-card.js
 * 
 * Card config:
 *   type: custom:smart-charging-card
 *   entity_prefix: gw_smart_charging   (optional, auto-detected)
 */
const CARD_VERSION = '3.2.0';

class SmartChargingCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) { this._init(); this._initialized = true; }
    this._update();
  }

  setConfig(config) {
    this._config = config;
    this._prefix = config.entity_prefix || 'gw_smart_charging';
  }

  static getStubConfig() {
    return { type: 'custom:smart-charging-card' };
  }

  getCardSize() { return 8; }

  _init() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
<style>
:host{display:block;font-family:var(--paper-font-body1_-_font-family,'Roboto',sans-serif)}
.card{background:var(--ha-card-background,var(--card-background-color,#1e2a3a));border-radius:var(--ha-card-border-radius,12px);
  padding:16px;color:var(--primary-text-color,#e8eaf0);box-shadow:var(--ha-card-box-shadow,0 2px 6px rgba(0,0,0,.3))}
.hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.hdr h2{font-size:1.1em;font-weight:600;margin:0;display:flex;align-items:center;gap:8px}
.hdr .ver{font-size:.65em;color:var(--secondary-text-color,#8892a4);font-weight:400}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:14px}
@media(max-width:500px){.grid{grid-template-columns:repeat(2,1fr)}}
.item{text-align:center;padding:10px 6px;background:rgba(255,255,255,.04);border-radius:8px}
.val{font-size:1.5em;font-weight:700;line-height:1.1}.unit{font-size:.36em;color:var(--secondary-text-color);margin-left:2px}
.lbl{font-size:.65em;color:var(--secondary-text-color);text-transform:uppercase;letter-spacing:.5px;margin-top:3px}
.bar{height:16px;background:rgba(255,255,255,.06);border-radius:4px;overflow:hidden;margin:8px 0;position:relative}
.bar-fill{height:100%;border-radius:4px;transition:width .5s}
.bar-txt{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:.65em;font-weight:700;color:rgba(0,0,0,.8)}
.green{color:#51cf66}.blue{color:#74c0fc}.purple{color:#a78bfa}.orange{color:#ffa94d}.red{color:#ff6b6b}.teal{color:#00d4aa}
.bg-green{background:linear-gradient(90deg,#51cf66,#69db7c)}.bg-yellow{background:linear-gradient(90deg,#ffa94d,#ffd43b)}.bg-red{background:linear-gradient(90deg,#ff6b6b,#f03e3e)}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:.7em;font-weight:600}
.b-on{background:rgba(81,207,102,.15);color:#69db7c;border:1px solid rgba(81,207,102,.3)}
.b-off{background:rgba(255,255,255,.06);color:var(--secondary-text-color);border:1px solid rgba(255,255,255,.1)}
.b-chg{background:rgba(81,207,102,.2);color:#69db7c;border:1px solid rgba(81,207,102,.4);animation:pulse 2s infinite}
.b-nt{background:rgba(0,212,170,.15);color:#00d4aa;border:1px solid rgba(0,212,170,.3)}
.b-vt{background:rgba(255,107,107,.12);color:#ff8787;border:1px solid rgba(255,107,107,.25)}
.section{margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,.07)}
.section h3{font-size:.78em;font-weight:600;margin:0 0 8px;color:var(--secondary-text-color);text-transform:uppercase;letter-spacing:.5px}
.slots{font-size:.76em}.slot{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.slot:last-child{border-bottom:none}.slot-time{font-weight:600}.slot-price{color:#a78bfa}.slot-soc{color:#51cf66}
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;font-size:.72em}
.stat{text-align:center;padding:6px;background:rgba(255,255,255,.03);border-radius:6px}
.stat-v{font-size:1.2em;font-weight:700}.stat-l{color:var(--secondary-text-color);font-size:.8em;margin-top:2px}
.ctrl{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.btn{padding:6px 14px;border:none;border-radius:8px;font-size:.75em;font-weight:600;cursor:pointer;color:#fff}
.btn-on{background:#34a853}.btn-off{background:#e53935}.btn-blue{background:#1e88e5}
.btn:hover{filter:brightness(1.15)}
.err{color:#ff8787;font-size:.76em;padding:6px;background:rgba(255,107,107,.1);border-radius:6px;margin-bottom:8px}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
</style>
<div class="card">
  <div class="hdr">
    <h2>⚡ Smart Charging <span class="ver">v${CARD_VERSION}</span></h2>
    <div id="status"></div>
  </div>
  <div id="error"></div>
  <div class="grid" id="grid"></div>
  <div class="bar" id="bar-wrap"><div class="bar-fill" id="bar"></div><div class="bar-txt" id="bar-txt"></div></div>
  <div class="section"><h3>📋 Nabíjecí sloty</h3><div class="slots" id="slots"></div></div>
  <div class="section"><h3>📈 Statistiky</h3><div class="stats-row" id="stats"></div></div>
  <div class="section ctrl" id="ctrl"></div>
</div>`;
    this._pollData();
    this._interval = setInterval(() => this._pollData(), 30000);
  }

  async _pollData() {
    try {
      const r = await fetch('/api/gw_smart_charging/data');
      if (r.ok) { this._apiData = await r.json(); this._update(); }
    } catch (e) { /* silent */ }
  }

  _update() {
    if (!this._hass || !this.shadowRoot) return;
    const d = this._apiData || {};
    const bat = d.battery || {};
    const plan = d.plan || {};
    const slots = plan.slots || [];
    const ti = d.tariff_info || {};
    const hdo = d.hdo || {};
    const st = d.statistics || {};
    const cf = d.consumption_forecast || {};
    const fc = d.price_forecast || {};
    const pl = fc.prices || [];

    // Error
    const errEl = this.shadowRoot.getElementById('error');
    if (d.errors && d.errors.length) {
      errEl.innerHTML = `<div class="err">⚠️ ${d.errors.join(' | ')}</div>`;
    } else { errEl.innerHTML = ''; }

    // Status badges
    const statusEl = this.shadowRoot.getElementById('status');
    let badges = '';
    if (d.charging_active) badges += '<span class="badge b-chg">⚡ NABÍJÍ</span> ';
    else if (d.auto_enabled) badges += '<span class="badge b-on">Auto ON</span> ';
    else badges += '<span class="badge b-off">Auto OFF</span> ';
    if (ti.current_nt != null) badges += `<span class="badge ${ti.current_nt ? 'b-nt' : 'b-vt'}">${ti.current_nt ? 'NT' : 'VT'}</span>`;
    statusEl.innerHTML = badges;

    // Battery bar
    const soc = bat.soc;
    const barEl = this.shadowRoot.getElementById('bar');
    const barTxt = this.shadowRoot.getElementById('bar-txt');
    if (soc != null) {
      barEl.style.width = soc + '%';
      barEl.className = 'bar-fill ' + (soc < 30 ? 'bg-red' : soc < 70 ? 'bg-yellow' : 'bg-green');
      barTxt.textContent = soc.toFixed(0) + '%';
    }

    // Current price from forecast
    const nowKey = this._localKeyH(new Date());
    const curP = pl.find(p => (p.time || '').substring(0, 13) === nowKey);

    // Grid items
    const gridEl = this.shadowRoot.getElementById('grid');
    gridEl.innerHTML = [
      this._item(soc != null ? soc.toFixed(1) : '—', '%', 'SOC', 'green'),
      this._item(bat.power != null ? Math.abs(bat.power).toFixed(0) : '—', 'W', bat.charging ? '⚡ Nabíjí' : bat.discharging ? '⬇️ Vybíjí' : 'Výkon', 'blue'),
      this._item(curP ? curP.total_price.toFixed(2) : '—', 'CZK', 'Celk. cena', 'purple'),
      this._item(slots.length, 'sl', 'Plán', 'orange'),
      this._item(cf.total_24h_kwh || '—', 'kWh', 'Spotř. 24h', 'teal'),
      this._item((st.today || {}).cost_czk || '0', 'CZK', 'Dnes', 'red'),
      this._item(((st.month || {}).total_cost_czk || 0).toFixed(0), 'CZK', 'Měsíc', 'purple'),
      this._item(((st.month || {}).nt_share_pct || 0) + '%', '', 'NT podíl', 'teal'),
    ].join('');

    // Slots
    const slotsEl = this.shadowRoot.getElementById('slots');
    if (slots.length === 0) {
      slotsEl.innerHTML = '<div style="color:var(--secondary-text-color);font-style:italic">Žádné sloty</div>';
    } else {
      slotsEl.innerHTML = slots.slice(0, 6).map(s => 
        `<div class="slot"><span class="slot-time">${s.start} → ${(s.end||'').substring(11,16)}</span>` +
        `<span class="slot-price">${parseFloat(s.total_price).toFixed(4)} CZK</span>` +
        `<span class="slot-soc">→ ${s.target_soc}%</span></div>`
      ).join('');
    }

    // Statistics
    const statsEl = this.shadowRoot.getElementById('stats');
    const wk = st.week || {}, mn = st.month || {};
    statsEl.innerHTML = [
      this._stat((st.today || {}).cost_czk || 0, 'Dnes', 'red'),
      this._stat(wk.total_cost_czk || 0, 'Týden', 'orange'),
      this._stat(mn.total_cost_czk || 0, 'Měsíc', 'purple'),
      this._stat((mn.avg_price_czk_kwh || 0).toFixed(2), 'Ø CZK/kWh', 'teal'),
    ].join('');

    // Controls
    const ctrlEl = this.shadowRoot.getElementById('ctrl');
    ctrlEl.innerHTML = `
      <button class="btn btn-on" id="b-on">✓ Auto ON</button>
      <button class="btn btn-off" id="b-off">✗ Auto OFF</button>
      <button class="btn btn-blue" id="b-ref">🔄 Přepočítat</button>
      <a href="/api/gw_smart_charging/dashboard" target="_blank" class="btn btn-blue" style="text-decoration:none">📊 Dashboard</a>`;
    this.shadowRoot.getElementById('b-on').onclick = () => this._cmd('on');
    this.shadowRoot.getElementById('b-off').onclick = () => this._cmd('off');
    this.shadowRoot.getElementById('b-ref').onclick = () => this._refresh();
  }

  _item(val, unit, label, color) {
    return `<div class="item"><div class="val ${color}">${val}<span class="unit">${unit}</span></div><div class="lbl">${label}</div></div>`;
  }

  _stat(val, label, color) {
    return `<div class="stat"><div class="stat-v ${color}">${typeof val === 'number' ? val.toFixed(1) : val}</div><div class="stat-l">${label}</div></div>`;
  }

  _localKeyH(d) {
    const y = d.getFullYear(), m = String(d.getMonth() + 1).padStart(2, '0'),
          dd = String(d.getDate()).padStart(2, '0'), h = String(d.getHours()).padStart(2, '0');
    return `${y}-${m}-${dd} ${h}`;
  }

  async _cmd(state) {
    try { await fetch(`/api/gw_smart_charging/auto/${state}`, { method: 'POST' }); setTimeout(() => this._pollData(), 1000); } catch (e) {}
  }

  async _refresh() {
    try { await fetch('/api/gw_smart_charging/refresh', { method: 'POST' }); setTimeout(() => this._pollData(), 5000); } catch (e) {}
  }

  disconnectedCallback() {
    if (this._interval) clearInterval(this._interval);
  }
}

customElements.define('smart-charging-card', SmartChargingCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'smart-charging-card',
  name: 'Smart Battery Charging',
  description: 'Inteligentní řízení nabíjení baterie s distribučními tarify a statistikami',
  preview: true,
});

console.info(`%c SMART-CHARGING-CARD v${CARD_VERSION} `, 'color:#fff;background:#6c63ff;font-weight:700;padding:4px 8px;border-radius:4px');
