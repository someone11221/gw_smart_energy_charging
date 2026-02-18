# 🚀 Nahrání na GitHub

## Příprava (jednorázově)

```bash
# 1. Nainstaluj git (pokud nemáš)
sudo apt install git

# 2. Nastav identitu
git config --global user.name "Martin Rak"
git config --global user.email "tvuj@email.cz"

# 3. Vytvoř nový repozitář na GitHub:
#    https://github.com/new
#    Název: gw_smart_energy_charging
#    Visibility: Public (pro HACS)
#    NEvytvářej README/LICENSE (máme vlastní)
```

## Upload

```bash
# 4. Rozbal repo ZIP a vstup do složky
unzip gw_smart_charging_v3.2.0_repo.zip -d gw_smart_energy_charging
cd gw_smart_energy_charging

# 5. Inicializuj git
git init
git add .
git commit -m "v3.2.0: Smart Battery Charging Controller

- Czech spot price optimization (OTE/Nanogreen)
- Distribution tariffs (EG.D/ČEZ/PRE)
- HDO signal, adaptive consumption prediction
- Debug system, fallback mode, Lovelace card
- 7 sensors, persistent statistics, config validation"

# 6. Napoj na GitHub a pushni
git remote add origin https://github.com/someone11221/gw_smart_energy_charging.git
git branch -M main
git push -u origin main

# 7. Vytvoř release tag
git tag -a v3.2.0 -m "v3.2.0 — HDO, adaptive learning, debug, fallback"
git push --tags
```

## GitHub Release (volitelné, ale doporučené pro HACS)

1. Na GitHubu přejdi na **Releases → Create new release**
2. Vyber tag `v3.2.0`
3. Název: `v3.2.0 — Smart Battery Charging Controller`
4. Nahraj `gw_smart_charging_v3.2.0.zip` jako asset
5. Publikuj

## HACS registrace

Po nahrání na GitHub mohou ostatní přidat repo přes:
**HACS → ⋮ → Vlastní repozitáře → URL: `https://github.com/someone11221/gw_smart_energy_charging` → Kategorie: Integrace**

## Aktualizace v budoucnu

```bash
cd gw_smart_energy_charging
# ... uprav soubory ...
git add .
git commit -m "v3.2.1: popis změn"
git tag v3.2.1
git push && git push --tags
```
