"""Translation support for GW Smart Charging."""

from typing import Dict

# Translation dictionaries
TRANSLATIONS = {
    "en": {
        # Strategies
        "strategy_dynamic": "Dynamic Optimization",
        "strategy_dynamic_desc": "Smart optimization based on prices, forecasts, and ML patterns",
        "strategy_4_lowest": "4 Lowest Hours",
        "strategy_4_lowest_desc": "Charge during 4 cheapest hours in next 24h",
        "strategy_6_lowest": "6 Lowest Hours",
        "strategy_6_lowest_desc": "Charge during 6 cheapest hours in next 24h",
        "strategy_nanogreen": "Nanogreen Only",
        "strategy_nanogreen_desc": "Use only Nanogreen sensor for decisions",
        "strategy_price_threshold": "Price Threshold",
        "strategy_price_threshold_desc": "Charge whenever price below threshold",
        "strategy_adaptive_smart": "Adaptive Smart",
        "strategy_adaptive_smart_desc": "Learns from past consumption patterns",
        "strategy_solar_priority": "Solar Priority",
        "strategy_solar_priority_desc": "Maximize solar self-consumption",
        "strategy_peak_shaving": "Peak Shaving",
        "strategy_peak_shaving_desc": "Avoid grid during peak hours",
        "strategy_tou_optimized": "Time-of-Use Optimized",
        "strategy_tou_optimized_desc": "Optimized for TOU tariffs",
        
        # Dashboard
        "dashboard_title": "GW Smart Charging Dashboard",
        "battery_status": "Battery Status",
        "soc": "State of Charge",
        "charging_mode": "Charging Mode",
        "current_price": "Current Price",
        "next_charge": "Next Charge",
        "today_charged": "Today Charged",
        "today_discharged": "Today Discharged",
        "integration_status": "Integration Status",
        "active": "Active",
        "inactive": "Inactive",
        "activate": "Activate",
        "deactivate": "Deactivate",
        "configuration": "Configuration",
        "statistics": "Statistics",
        "24h_prediction": "24-Hour Prediction",
        "price_chart": "Price Chart",
        "energy_flow": "Energy Flow",
        "settings": "Settings",
        "language": "Language",
        
        # Charging modes
        "mode_grid_charge": "Grid Charging",
        "mode_solar_charge": "Solar Charging",
        "mode_battery_discharge": "Battery Discharge",
        "mode_self_consume": "Self Consumption",
        "mode_idle": "Idle",
        
        # Common
        "yes": "Yes",
        "no": "No",
        "enabled": "Enabled",
        "disabled": "Disabled",
        "save": "Save",
        "cancel": "Cancel",
        "close": "Close",
        "kwh": "kWh",
        "czk_kwh": "CZK/kWh",
        "percent": "%",
        "hour": "hour",
        "hours": "hours",
    },
    "cs": {
        # Strategies
        "strategy_dynamic": "Dynamická optimalizace",
        "strategy_dynamic_desc": "Chytrá optimalizace založená na cenách, předpovědích a ML vzorcích",
        "strategy_4_lowest": "4 nejlevnější hodiny",
        "strategy_4_lowest_desc": "Nabíjení během 4 nejlevnějších hodin v příštích 24h",
        "strategy_6_lowest": "6 nejlevnějších hodin",
        "strategy_6_lowest_desc": "Nabíjení během 6 nejlevnějších hodin v příštích 24h",
        "strategy_nanogreen": "Pouze Nanogreen",
        "strategy_nanogreen_desc": "Použít pouze Nanogreen senzor pro rozhodování",
        "strategy_price_threshold": "Cenový práh",
        "strategy_price_threshold_desc": "Nabíjení kdykoli cena klesne pod práh",
        "strategy_adaptive_smart": "Adaptivní chytrá",
        "strategy_adaptive_smart_desc": "Učí se ze vzorců minulé spotřeby",
        "strategy_solar_priority": "Priorita solární",
        "strategy_solar_priority_desc": "Maximalizace vlastní spotřeby ze solárů",
        "strategy_peak_shaving": "Redukce špiček",
        "strategy_peak_shaving_desc": "Vyhýbání se síti během špičky",
        "strategy_tou_optimized": "Optimalizace TOU",
        "strategy_tou_optimized_desc": "Optimalizováno pro TOU tarify",
        
        # Dashboard
        "dashboard_title": "GW Smart Charging Dashboard",
        "battery_status": "Stav baterie",
        "soc": "Stav nabití",
        "charging_mode": "Režim nabíjení",
        "current_price": "Aktuální cena",
        "next_charge": "Další nabíjení",
        "today_charged": "Dnes nabito",
        "today_discharged": "Dnes vybito",
        "integration_status": "Stav integrace",
        "active": "Aktivní",
        "inactive": "Neaktivní",
        "activate": "Aktivovat",
        "deactivate": "Deaktivovat",
        "configuration": "Konfigurace",
        "statistics": "Statistiky",
        "24h_prediction": "24h predikce",
        "price_chart": "Graf cen",
        "energy_flow": "Tok energie",
        "settings": "Nastavení",
        "language": "Jazyk",
        
        # Charging modes
        "mode_grid_charge": "Nabíjení ze sítě",
        "mode_solar_charge": "Nabíjení ze solárů",
        "mode_battery_discharge": "Vybíjení baterie",
        "mode_self_consume": "Vlastní spotřeba",
        "mode_idle": "Nečinný",
        
        # Common
        "yes": "Ano",
        "no": "Ne",
        "enabled": "Povoleno",
        "disabled": "Zakázáno",
        "save": "Uložit",
        "cancel": "Zrušit",
        "close": "Zavřít",
        "kwh": "kWh",
        "czk_kwh": "CZK/kWh",
        "percent": "%",
        "hour": "hodina",
        "hours": "hodin",
    }
}


def get_translation(key: str, language: str = "cs") -> str:
    """Get translation for a key in specified language.
    
    Args:
        key: Translation key
        language: Language code (cs or en), defaults to cs
        
    Returns:
        Translated string or key if not found
    """
    if language not in TRANSLATIONS:
        language = "cs"
    
    return TRANSLATIONS[language].get(key, key)


def get_all_translations(language: str = "cs") -> Dict[str, str]:
    """Get all translations for specified language.
    
    Args:
        language: Language code (cs or en), defaults to cs
        
    Returns:
        Dictionary of all translations
    """
    if language not in TRANSLATIONS:
        language = "cs"
    
    return TRANSLATIONS[language]
