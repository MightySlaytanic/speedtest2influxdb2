# speedtest-monitoring
Speedtest stats' uploader to InfluxDB2

**DISCLAIMER**: avoid launching it too frequently to avoid issues with your provider or charges if on paid connections. The tool transfers hundreds of MBs at each launch

## Requirements

The script requires the module influxdb-client to be installed on your host with pip and speedtest cli tool from Ookla (not the speedtest-cli found in standard Debian repos)

```bash
#--- Instructions from Ookla: https://www.speedtest.net/apps/cli ---#
## If migrating from prior bintray install instructions please first...
# sudo rm /etc/apt/sources.list.d/speedtest.list
# sudo apt-get update
# sudo apt-get remove speedtest
## Other non-official binaries will conflict with Speedtest CLI
# Example how to remove using apt-get
# sudo apt-get remove speedtest-cli
sudo apt-get install curl
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt-get install speedtest
#--- End Instructions from Ookla ---#

apt install pip3
pip3 install influxdb-client
```

**IMPORTANT**: launch speedtest at least once interactively to accept license agreement before running it as a background script.

A functioning InfluxDB v2 instance hosted on your local LAN is required too.

## Script Overview

### speedtest_stats_to_influxdb2.py 

The script launches a speedtest run to the best server it guesses from your network location or to the server specified via SPEEDTEST_SERVER_ID environment variable,
outputs stats in JSON format and processes it uploading the following info to an InfluxDB2 bucket (you can see this output without uploading data to InfluxDB2 by passing
-t to the python script, or to the wrapper shown in a later section):

```json
Measurements for host MY_HOST
[
    {
        "measurement": "ping",
        "tags": {
            "host": "MY_HOST",
            "server_desc": "Konverto AG (Bolzano)"
        },
        "fields": {
            "jitter": 0.809,
            "latency": 3.526,
            "low": 3.061,
            "high": 4.639
        }
    },
    {
        "measurement": "bandwidth",
        "tags": {
            "host": "MY_HOST",
            "server_desc": "Konverto AG (Bolzano)"
        },
        "fields": {
            "download_bps": 877964120,
            "upload_bps": 258158152
        }
    },
    {
        "measurement": "packet_loss",
        "tags": {
            "host": "MY_HOST",
            "server_desc": "Konverto AG (Bolzano)"
        },
        "fields": {
            "packet_loss": 0.0
        }
    }
]
```

## Usage

### Variables

The script requires you to set some environment variables: you can set them directly within the python script or prepare a 
wrapper shell script that sets the environment variables and then launches speedtest_stats_to_influxdb2.py as explained later.

| Variable | Description |
| ----- | ----- |
| INFLUX_HOST | The host URL or IP for your InfluxDb instance|
| INFLUX_PORT | The port for your InfluxDB instance |
| INFLUX_TOKEN | The admin token for your InfluxDB instance |
| INFLUX_ORGANIZATION | Your InfluxDB Org Name |
| INFLUX_BUCKET | Your InfluxDB Bucket Name |
| HOST_TAG | The name of your Host |
| SPEEDTEST_COMMAND | Path to the installed speedtest cli (found with *which speedtest*) |
| SPEEDTEST_SERVER_ID | Server ID for the choosen server: leave it unset or set to "" to allow for automatic selection of the server |
| SPEEDTEST_SERVER_DESCRIPTION | Server description: if unset or set to "" is taken from speedtest output |

### Wrapper script

Follows an example of wrapper script that can be used to launch the python script with Environment variables correctly set:

```bash
nano /path-to-scripts/launch_speedtest2influxdb2.sh

#!/bin/bash

export INFLUX_HOST="INFLUX_IP"
export INFLUX_PORT=8086
export INFLUX_ORGANIZATION="influx_org"
export INFLUX_BUCKET="influx_bucket"
export INFLUX_SERVICE_TAG="influx_service_tag"
export INFLUX_TOKEN="influx_token"
export HOST_TAG="host-tag"

export SPEEDTEST_COMMAND="/usr/bin/speedtest -f json"
export SPEEDTEST_SERVER_ID="25254"
export SPEEDTEST_SERVER_DESCRIPTION="Konverto AG (Bolzano)"

python3 /opt/speedtest2influxdb2/speedtest_stats_to_influxdb2.py $*

# Save the file and make it executable
chmod +x /path-to-scripts/launch_speedtest2influxdb2.sh
```

### Scheduling a speedtest every X hours

You can then setup a crontab entry to execute the speedtest and upload data to InfluxDB2 every X hours. For example, to test every 4 hours:

```bash
nano /etc/cron.d/speedtest-monitoring

# Upload stats to InfluxDB2

* */4 * * * root /path-to-scripts/pve_disks_stats_to_influxdb2.sh >/dev/null 2>&1
```

