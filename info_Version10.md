```markdown
# GW Smart Charging

GW Smart Charging automatizuje nabíjení baterie přes GoodWe invertor podle hodinových cen a solárního forecastu.

Co dělá
- 24-hodinový plán nabíjení (mode: pv / grid / idle).
- UI config flow (přidání přes Settings → Devices & Services → Add integration).
- Služby:
  - gw_smart_charging.optimize_now
  - gw_smart_charging.apply_schedule_now

Screenshot
- Přidejte screenshot do `.github/assets/` (např. `.github/assets/screenshot.png`) a upravte odkaz níže:
  ![screenshot](https://raw.githubusercontent.com/someone11221/gw_smart_energy_charging/main/.github/assets/screenshot.png)

Instalace přes HACS
1. HACS → Settings → Custom repositories → Add repository  
   - Repository URL: https://github.com/someone11221/gw_smart_energy_charging  
   - Category: Integration  
2. Po instalaci restartujte Home Assistant.  
3. Settings → Devices & Services → Add Integration → GW Smart Charging

Ladění
- Dočasné zapnutí debug logování (v configuration.yaml):
```yaml
logger:
  default: warning
  logs:
    custom_components.gw_smart_charging: debug
    homeassistant.config_entries: debug
```

Kontakt / podpora
- Issues: https://github.com/someone11221/gw_smart_energy_charging/issues
```