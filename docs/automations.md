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

## 🏠 Welcome Home when Arriving

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

## ⚠️ Vehicle Fault Alert

Notify when new diagnostic fault codes appear:

```yaml
alias: "Alert on vehicle faults"
trigger:
  - platform: state
    entity_id: binary_sensor.vehicle_active_faults
    from: "off"
    to: "on"
action:
  - service: notify.mobile_app_simone
    data:
      title: "⚠️ Vehicle Alert"
      message: >
        New faults detected:
        {{ state_attr('binary_sensor.vehicle_active_faults', 'faults_list') | join(', ') }}
```

## 🚗 Engine Running for Too Long

Alert when vehicle idles with engine on for extended periods:

```yaml
alias: "Long idle warning"
trigger:
  - platform: state
    entity_id: binary_sensor.vehicle_ignition
    to: "on"
    for:
      minutes: 60
condition:
  - condition: state
    entity_id: binary_sensor.vehicle_driving
    state: "off"
action:
  - service: notify.mobile_app_simone
    data:
      title: "⏱️ Idle Alert"
      message: "Vehicle engine has been running for over an hour while parked."
```
