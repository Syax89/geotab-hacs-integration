# Automation Examples 🤖

Here are some ways you can use Geotab data in your Home Assistant automations.

## ⛽ Low Fuel Notification
```yaml
alias: "Notify when fuel is low"
trigger:
  - platform: numeric_state
    entity_id: sensor.vehicle_fuel_level
    below: 15
action:
  - service: notify.mobile_app_simone
    data:
      title: "Fuel Alert"
      message: "Your vehicle has only {{ states('sensor.vehicle_fuel_level') }}% fuel left."
```

## 🏠 Welcome Home when arriving
```yaml
alias: "Turn on lights when arriving home"
trigger:
  - platform: zone
    entity_id: device_tracker.vehicle_location
    zone: zone.home
    event: enter
action:
  - service: light.turn_on
    target:
      entity_id: light.garage_lights
```
