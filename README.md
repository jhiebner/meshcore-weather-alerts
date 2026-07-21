# MeshCore Weather Alerts

MeshCore Weather Alerts is a Python application that watches the National Weather Service (NWS) for severe weather alerts and broadcasts them over a MeshCore network.

## What this project does

The gateway:
- checks the NWS for active alerts
- filters alerts by your location and selected alert types
- sends the messages over your MeshCore device
- can run in the foreground or as a background service

## Requirements

- Ubuntu 22.04 or newer
- Python 3.10+
- Internet connection
- A MeshCore device connected by serial port

## Quick start

If you are new to this project, the easiest path is:

1. Install the package and dependencies
2. Run the quick-start flow
3. Start using the gateway

### 1. Install dependencies

From the project directory:

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

### 2. Run quick-start

```bash
meshcore-weather quick-start
```

This will:
- run the setup wizard if needed
- install the service unit
- enable the service
- start the service

If you ever need to change your configuration later, you can run:

```bash
meshcore-weather --setup
```

The wizard will ask for:
- the MeshCore serial port
- your latitude and longitude
- which alert types to broadcast
- the MeshCore channel
- polling and repeat intervals

### 3. Validate the configuration

```bash
meshcore-weather validate
```

### 4. Start the gateway

For a one-time test run:

```bash
meshcore-weather test
```

For a foreground run:

```bash
meshcore-weather run
```

For a background service setup:

```bash
meshcore-weather quick-start
```

## Command reference

### Setup and configuration

- `meshcore-weather --setup`
  - Launches the interactive setup wizard for changing configuration values later.

- `meshcore-weather validate`
  - Checks that your configuration file is complete and valid.

### Running the gateway

- `meshcore-weather run`
  - Starts the gateway in the foreground.

- `meshcore-weather service`
  - Starts the gateway in the background as a detached process.

- `meshcore-weather stop`
  - Stops the background gateway process started by `service`.

### Systemd service management

- `meshcore-weather install`
  - Installs the systemd service unit file.

- `meshcore-weather enable`
  - Enables the service so it starts at boot.

- `meshcore-weather start`
  - Starts the systemd service now.

- `meshcore-weather stop`
  - Stops the running systemd service.

- `meshcore-weather status`
  - Shows the current status of the systemd service.

- `meshcore-weather quick-start`
  - Runs setup if needed, then installs, enables, and starts the service.

### Testing

- `meshcore-weather test`
  - Sends a test alert or forecast message using the current configuration.

### Version

- `meshcore-weather --version`
  - Prints the installed version number.

## Recommended beginner workflow

If you are setting this up for the first time, this is the easiest path:

```bash
meshcore-weather quick-start
meshcore-weather validate
```

That sequence will:
1. configure the program if needed
2. install the service
3. enable it
4. start it in the background
5. verify the config

## Notes

- The gateway uses your latitude and longitude to determine which local weather zones should be considered.
- If you enter `0` for the repeat interval, repeat broadcasts will be disabled.
- If the MeshCore serial port cannot be reached, the setup wizard will prompt you again until a working port is entered.

## License

MIT License
