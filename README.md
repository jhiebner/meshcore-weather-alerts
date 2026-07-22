# MeshCore Weather Alerts

MeshCore Weather Alerts is a Python application that watches the National Weather Service (NWS) for severe weather alerts and broadcasts them over a MeshCore network.

## What this project does

The gateway:
- checks the NWS for active alerts
- filters alerts by your location and selected alert types
- sends the messages over your MeshCore device
- can run in the foreground or as a systemd-managed service

## Requirements

- Ubuntu 22.04 or newer
- Python 3.10+
- Internet connection
- A MeshCore device connected by serial port


Installation process:

```bash
sudo apt update
sudo apt install -y python3-pip git

git clone https://github.com/jhiebner/meshcore-weather-alerts.git
cd meshcore-weather-alerts

python3 -m pip install --upgrade pip
python3 -m pip install meshcore-cli
sudo python3 -m pip install .
```

For systemd usage (`quick-start`, `install`, `enable`, `start`), `meshcore-weather` must be installed system-wide so the service runs outside any virtual environment.

If you are developing or testing this project, install developer tools with:

```bash
python3 -m pip install -r requirements-dev.txt
```


Before running the weather gateway setup, open `meshcore-cli` and create the MeshCore channel you want the weather alerts to use. "/dev/ttyACM0" is the device port path, you will need to find you specific path, you will need it the quick-start config. 

```bash
meshcli -s /dev/ttyACM0
```

After you get into the CLI, add the channel you want to use:

```bash
add_channel {name_of_your_channel}
```

For example:

```bash
add_channel #weather-alerts
```

Then verify the channel was created:

```bash
get_channels
```

Your new channel should appear in the list and is now ready to be used by MeshCore Weather Alerts.

Exit meshcli by typing:

```bash
quit
```

### To start the meshcore-weather service:

### 1. Run the setup and start the service

```bash
meshcore-weather quick-start
```

This command will:
- start the interactive setup wizard if your configuration is missing
- install the systemd service unit
- enable the service so it starts at boot
- start the service right away

The setup wizard will ask you to choose from the MeshCore channels you already created in `meshcore-cli`.
If the channel does not exist yet, create it first in `meshcore-cli` before you continue.

The setup wizard will ask for:
- the MeshCore serial port
- your latitude and longitude
- which alert types to broadcast
- the MeshCore channel
- polling and repeat intervals

If you want to change those settings later, run:

```bash
meshcore-weather --setup
```

### 2. Validate the configuration

```bash
meshcore-weather validate
```

### 3. Choose how to run it

For a one-time test run:

```bash
meshcore-weather test
```

For a foreground run:

```bash
meshcore-weather run
```

For the systemd-managed background service that keeps running after you close the terminal:

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


## Notes

- The gateway uses your latitude and longitude to determine which local weather zones should be considered.
- If you enter `0` for the repeat interval, repeat broadcasts will be disabled.
- If the MeshCore serial port cannot be reached, the setup wizard will prompt you again until a working port is entered.

## License

MIT License
