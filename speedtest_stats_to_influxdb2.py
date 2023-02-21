#!/usr/bin/python3

import json
import argparse
from os import getenv
from subprocess import run,PIPE

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError

INFLUX_HOST = getenv("INFLUX_HOST")
INFLUX_PORT = getenv("INFLUX_PORT")
INFLUX_TOKEN = getenv("INFLUX_TOKEN")
INFLUX_ORGANIZATION = getenv("INFLUX_ORGANIZATION")
INFLUX_BUCKET = getenv("INFLUX_BUCKET")
HOST = getenv("HOST_TAG")

SPEEDTEST_COMMAND = getenv("SPEEDTEST_COMMAND")
SPEEDTEST_SERVER_ID = getenv("SPEEDTEST_SERVER_ID")
SPEEDTEST_SERVER_DESCRIPTION = getenv("SPEEDTEST_SERVER_DESCRIPTION")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="Speedtest stats to influxdb2 uploader")

    parser.add_argument(
        "-t",
        "--test",
        help="Just print the results without uploading to influxdb2",
        action="store_true"
    )

    args = parser.parse_args()

    measurements = []

    server_option = ""
    if SPEEDTEST_SERVER_ID:
        server_option += f"--server-id {SPEEDTEST_SERVER_ID}"
        
    data = json.loads(run([f"{SPEEDTEST_COMMAND} -f json {server_option}"], stdout=PIPE, stderr=None, text=True, shell=True).stdout)

    #data = json.loads(TEST_OUTPUT)

    if not SPEEDTEST_SERVER_DESCRIPTION:
      SPEEDTEST_SERVER_DESCRIPTION = data["server"]["name"]

    ping_stats = {}
    for item in data["ping"].keys():
        ping_stats[item] = float(data["ping"][item])

    measurements.append({
        "measurement": "ping",
        "tags": {"host": HOST, "server_desc": SPEEDTEST_SERVER_DESCRIPTION},
        "fields": ping_stats
    })

    bandwidth_stats = {}
    bandwidth_stats["download_bps"] = int(data["download"]["bandwidth"]) * 8
    bandwidth_stats["upload_bps"] = int(data["upload"]["bandwidth"]) * 8

    measurements.append({
        "measurement": "bandwidth",
        "tags": {"host": HOST, "server_desc": SPEEDTEST_SERVER_DESCRIPTION},
        "fields": bandwidth_stats
    })

    measurements.append({
        "measurement": "packet_loss",
        "tags": {"host": HOST, "server_desc": SPEEDTEST_SERVER_DESCRIPTION},
        "fields": { "packet_loss" : float(data["packetLoss"]) }
    })

    if args.test:
        print(f"\nMeasurements for host {HOST}")
        print(json.dumps(measurements, indent=4))
    else:
        try:
            client = InfluxDBClient(url=f"http://{INFLUX_HOST}:{INFLUX_PORT}", token=INFLUX_TOKEN, org=INFLUX_ORGANIZATION, timeout=30000)
            write_api = client.write_api(write_options=SYNCHRONOUS)

            write_api.write(
                INFLUX_BUCKET,
                INFLUX_ORGANIZATION,
                measurements
            )

        except TimeoutError as e:
            failure = True
            print(e,file=sys.stderr)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TimeoutError: Could not upload data to {INFLUX_HOST}:{INFLUX_PORT} for host {HOST}",file=sys.stderr)
            exit(-1)
        except InfluxDBError as e:
            failure = True
            print(e,file=sys.stderr)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] InfluxDBError: Could not upload data to {INFLUX_HOST}:{INFLUX_PORT} for host {HOST}",file=sys.stderr)
            exit(-1)
        except Exception as e:
            failure = True
            print(e, file=sys.stderr)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connection Error: Could not upload data to {INFLUX_HOST}:{INFLUX_PORT} for host {HOST}",file=sys.stderr)
            exit(-1)

        client.close()
