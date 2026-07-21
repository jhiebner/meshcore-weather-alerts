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

## Run from a local checkout

If you want to run the project directly from the GitHub repository on a fresh Ubuntu machine, use these steps:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git

git clone https://github.com/jhiebner/meshcore-weather-alerts.git
cd meshcore-weather-alerts

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

You can start the CLI directly from the repository root with:

```bash
python -m meshcore_weather.main quick-start
```

This runs the app from source and does not require installing it with pip.

If you are new to this project, the easiest path is:

### 1. Run the setup and start the service

```bash
python -m meshcore_weather.main quick-start
```

This command will:
- start the interactive setup wizard if your configuration is missing
- install the systemd service unit
- enable the service so it starts at boot
- start the service right away

The setup wizard will ask for:
- the MeshCore serial port
- your latitude and longitude
- which alert types to broadcast
- the MeshCore channel
- polling and repeat intervals

If you want to change those settings later, run:

```bash
python -m meshcore_weather.main --setup
```

### 2. Validate the configuration

```bash
python -m meshcore_weather.main validate
```

### 3. Choose how to run it

For a one-time test run:

```bash
python -m meshcore_weather.main test
```

For a foreground run:

```bash
python -m meshcore_weather.main run
```

For a background service that keeps running after you close the terminal:

```bash
python -m meshcore_weather.main quick-start
```

## Command reference

### Setup and configuration

- `python -m meshcore_weather.main --setup`
  - Launches the interactive setup wizard for changing configuration values later.

- `python -m meshcore_weather.main validate`
  - Checks that your configuration file is complete and valid.

### Running the gateway

- `python -m meshcore_weather.main run`
  - Starts the gateway in the foreground.

- `python -m meshcore_weather.main service`
  - Starts the gateway in the background as a detached process.

- `python -m meshcore_weather.main stop`
  - Stops the background gateway process started by `service`.

### Systemd service management

- `python -m meshcore_weather.main install`
  - Installs the systemd service unit file.

- `python -m meshcore_weather.main enable`
  - Enables the service so it starts at boot.

- `python -m meshcore_weather.main start`
  - Starts the systemd service now.

- `python -m meshcore_weather.main stop`
  - Stops the running systemd service.

- `python -m meshcore_weather.main status`
  - Shows the current status of the systemd service.

- `python -m meshcore_weather.main quick-start`
  - Runs setup if needed, then installs, enables, and starts the service.

### Testing

- `python -m meshcore_weather.main test`
  - Sends a test alert or forecast message using the current configuration.

### Version

- `python -m meshcore_weather.main --version`
  - Prints the installed version number.

## Recommended beginner workflow

If you are setting this up for the first time, this is the easiest path:

```bash
python -m meshcore_weather.main quick-start
python -m meshcore_weather.main validate
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
