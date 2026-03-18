import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import mygeotab


def _get_required_env(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


async def analyze_live_data():
    username = _get_required_env("GEOTAB_USERNAME")
    password = _get_required_env("GEOTAB_PASSWORD")
    database = _get_required_env("GEOTAB_DATABASE")

    print(f"--- ANALISI PROFONDITA LIVE ({datetime.now(timezone.utc).isoformat()}) ---")
    api = mygeotab.API(username=username, password=password, database=database)
    try:
        await asyncio.to_thread(api.authenticate)
        devices = cast(list[dict[str, Any]], await asyncio.to_thread(api.get, "Device"))

        for device in devices:
            device_id = device["id"]
            print(f"\nVeicolo: {device['name']} ({device_id})")

            status_info = await asyncio.to_thread(
                api.get, "DeviceStatusInfo", search={"deviceSearch": {"id": device_id}}
            )
            status_info = cast(list[dict[str, Any]], status_info)
            if status_info:
                si = status_info[0]
                print(f"  [DeviceStatusInfo] Data: {si.get('dateTime')}")
                print(
                    f"  [DeviceStatusInfo] Accensione (isIgnitionOn): {si.get('isIgnitionOn')}"
                )
                print(f"  [DeviceStatusInfo] In movimento (isDriving): {si.get('isDriving')}")
                print(f"  [DeviceStatusInfo] Velocita: {si.get('speed')} km/h")

            log_records = await asyncio.to_thread(
                api.get, "LogRecord", search={"deviceSearch": {"id": device_id}}, resultsLimit=1
            )
            log_records = cast(list[dict[str, Any]], log_records)
            if log_records:
                lr = log_records[0]
                print(
                    "  [GPS Log] Ultima posizione: "
                    f"{lr.get('dateTime')} (Lat: {lr.get('latitude')}, Lon: {lr.get('longitude')})"
                )

            from_date = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()

            ignition_data = await asyncio.to_thread(
                api.get,
                "StatusData",
                search={
                    "deviceSearch": {"id": device_id},
                    "diagnosticSearch": {"id": "DiagnosticIgnitionId"},
                    "fromDate": from_date,
                },
                resultsLimit=5,
            )
            ignition_data = cast(list[dict[str, Any]], ignition_data)
            if ignition_data:
                ignition_data.sort(key=lambda x: x["dateTime"], reverse=True)
                latest_ign = ignition_data[0]
                print(
                    f"  [StatusData - Ignition] Ultimo cambio: {latest_ign['data']} "
                    f"alle {latest_ign['dateTime']}"
                )
            else:
                print("  [StatusData - Ignition] Nessun cambio rilevato negli ultimi 30 minuti.")

            rpm_data = await asyncio.to_thread(
                api.get,
                "StatusData",
                search={
                    "deviceSearch": {"id": device_id},
                    "diagnosticSearch": {"id": "DiagnosticEngineSpeedId"},
                    "fromDate": from_date,
                },
                resultsLimit=1,
            )
            rpm_data = cast(list[dict[str, Any]], rpm_data)
            if rpm_data:
                print(f"  [StatusData - RPM] Valore: {rpm_data[0]['data']} alle {rpm_data[0]['dateTime']}")
            else:
                print("  [StatusData - RPM] Nessun dato RPM ricevuto negli ultimi 30 minuti.")

    except Exception as err:
        print(f"ERRORE CRITICO: {err}")


if __name__ == "__main__":
    asyncio.run(analyze_live_data())
