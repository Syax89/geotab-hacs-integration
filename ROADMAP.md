# 🗺️ Geotab HACS Integration - Software Roadmap
**Project Manager:** Aurora ✨ | **Status:** v0.8.1

Ecco il piano di sviluppo tecnico per trasformare questa integrazione in un punto di riferimento per la community di Home Assistant.

---

## 🎯 Fase 1: Qualità e Stabilità (Core Hardening) - v0.9.x
*Obiettivo: Rendere il codice indistruttibile e conforme agli standard Gold di Home Assistant.*

- [ ] **Unit Testing Avanzato:** Implementare `pytest-homeassistant-custom-component` per testare non solo le API, ma anche la corretta creazione delle entità in HA.
- [ ] **GitHub Actions (CI/CD):** 
    - Auto-run dei test ad ogni commit.
    - Integrazione di `Pre-commit hooks` per forzare lo stile Black/Isort.
- [ ] **Gestione asincrona nativa:** Investigare se il wrapper `mygeotab` può essere reso totalmente non-blocking per evitare l'uso di `run_in_executor`.

## 🚀 Fase 2: Nuove Feature (Data Expansion) - v1.0.0
*Obiettivo: Estrarre ogni bit di informazione utile dal dispositivo GO.*

- [ ] **Supporto Multi-Account:** Gestire più istanze/database Geotab contemporaneamente.
- [ ] **Sensore Trip (Viaggio):** Creazione di un'entità che riassume l'ultimo viaggio (distanza, consumo, tempo di sosta).
- [ ] **Eventi di Manutenzione:** Sensore che calcola i giorni/km rimanenti al prossimo tagliando basandosi sulle regole Geotab.
- [ ] **Supporto Zone/Geofencing:** Sincronizzare le zone create su MyGeotab come `zone` in Home Assistant.

## 💎 Fase 3: User Experience & Ecosystem - v1.1.0
*Obiettivo: Rendere l'integrazione "bella" e facile da usare.*

- [ ] **Custom Cards:** Creare una bozza di card Lovelace specifica per visualizzare la telemetria del veicolo.
- [ ] **Services Support:** Implementare servizi HA per forzare l'aggiornamento o inviare messaggi al conducente (dove supportato dai dispositivi).
- [ ] **Documentazione Wiki:** Creare una guida completa su come risolvere i problemi di comunicazione tra GO Device e HA.

---

## 🛡️ Note del Project Manager
La priorità rimane la **resilienza**: un'integrazione che smette di funzionare o rallenta Home Assistant viene disinstallata subito. Ogni nuova funzione della Fase 2 deve passare i test della Fase 1 prima di essere pubblicata.

---
*Piano approvato da Aurora per Syax89.*
