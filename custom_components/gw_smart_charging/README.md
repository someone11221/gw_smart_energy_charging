# GW Smart Charging

Integrace propojuje GoodWe (goodwe integration) se solárním forecastem a cenami elektřiny (např. integrace nanogreencz) a optimalizuje nabíjení baterie tak, aby minimalizovala náklady.

Instalace:
1. Vytvoř složku `custom_components/gw_smart_charging` v konfiguraci Home Assistant.
2. Nakopíruj soubory z tohoto repozitáře.
3. Restartuj Home Assistant.
4. V Settings -> Devices & Services -> Add Integration -> GW Smart Charging vyplň požadované entity.

Konfigurace (config flow):
- forecast_sensor: sensor s 24hodinovou předpovědí PV (např. ha-open-meteo-solar-forecast).
- price_sensor: sensor s 24hodinovými cenami elektřiny (např. nanogreencz integration).
- pv_power_sensor: (volitelně) aktuální výkon FVE.
- goodwe_switch: switch entity (GoodWe) pro povolení/zakázání nabíjení ze sítě (default: switch.nabijeni_ze_site).
- soc_sensor: sensor pro stav nabití baterie (default: sensor.battery_state_of_charge).
- battery_capacity_kwh: kapacita baterie (default: 17).
- max_charge_power_kw: maximální nabíjecí výkon (nastavuje se v GoodWe; pole je informativní).
- charge_efficiency: nabíjecí efektivita (default: 0.95).
- min_reserve_pct: minimální rezervní SOC (default: 10%).
- enable_automation: povolit automatické přepínání switch (default true).

Jak to funguje:
- Integrace načte forecast a ceny pro následující den, spočítá, kolik kWh je potřeba do baterie do 100% (respektuje min_reserve).
- Preferuje využití PV během hodin s produkcí; nedostatek dobijí z gridu v nejlevnějsích hodinách (v rámci max_charge_power).
- Vystaví sensor forecast_next_day se schedule atributem (24 položek) — recorder uchová data v DB.
- Pokud je automation povolena, v každé hodině integrace aplikuje plán voláním switch.turn_on/turn_off na zvoleném GoodWe switchu.

Služby:
- gw_smart_charging.optimize_now — vynutí přepočet plánu.
- gw_smart_charging.apply_schedule_now — okamžitě aplikuje plán pro aktuální hodinu.

Poznámky:
- Před povolením automatiky doporučujeme testování a kontrolu mappingu GoodWe switch entity.
- Pokud chceš vlastní SQL tabulku nebo detailní logování, mohu přidat volitelnou funkcionalitu pro zápis do recorder vlastní tabulky nebo publikaci eventů.
