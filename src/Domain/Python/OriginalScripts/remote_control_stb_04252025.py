'''
* Created by TiViCon Co Ltd,.
*     https://www.tivicon.com
*     info@tivicon.com
*     Copyright (c) 2024 - 2025.
*     All rights reserved.
*
*     Unauthorized copying or redistribution of this file in source and binary forms via any medium
*     is strictly prohibited.
'''

VERSION = "25.04.2025"


'''
Changes:
25.04.2025

- Add some colors and types for faster navigation

16.04.2025

- Add CMD_GET_DVR_STATUS
- Add CMD_SEND_DVR_BUTTON_KEY

01.04.2025

- Add WOL command

28.03.2025

- Add CMD_REBOOT_STB


12.03.2025

- Use same UDP Port for Screenshots
- Add HELLO_DISCOVERY

14.02.2025
- Add support for 8 - FORCE SET CH SOURCE
- Add support for 10 - GET RECORDING CURRENT PLAYBACK STATUS
- Add support for - ALLOW_PLAYBACK - immediately allow channel playback

'''

import socket
import os
import struct

import json
import random
import uuid
from datetime import datetime, timedelta, timezone
import base64
import gzip
from io import BytesIO
import threading


# Unique STB ID
device_id = "750051288"

# Static IP Address of STB We are sending message
device_ip = "10.30.5.148"
# MAC Address of STB to send WOL message
device_mac = "ac:f4:2c:99:2f:51"

# Static port - DO NOT CHANGE
port = 25671

# Pernament API key used for Fanthom
api_key = "dca15ceb-39c9-49f8-a0a6-a85c7402af6e"

# Set default directory for screenshots
output_dir = "./screenshots/"

# Generate a random UUID
# NOT USED as it is too long.
def generate_uuid():
    unique_id = uuid.uuid4()  # uuid4 generates a random UUID
    return int(unique_id)

def generate_8_digit_integer():
    return random.randint(1, 99999999)

# Get current timestamp in GMT+2 and add 20 seconds (test purpuse) Please adjust your time to sync it with STB time !
def get_trigger_time():
    gmt_plus_2 = timezone(timedelta(hours=2))  # Define GMT+2
    current_time = datetime.now(gmt_plus_2) + timedelta(seconds=20)
    return int(current_time.timestamp())

def get_start_rec_time():
    gmt_plus_2 = timezone(timedelta(hours=2))  # Define GMT+2
    current_time = datetime.now(gmt_plus_2) + timedelta(seconds=40)
    return int(current_time.timestamp())

def get_stop_rec_time():
    gmt_plus_2 = timezone(timedelta(hours=2))  # Define GMT+2
    current_time = datetime.now(gmt_plus_2) + timedelta(seconds=80)
    return int(current_time.timestamp())

"""
Send a Wake-on-LAN (WOL) magic packet.

Args:
    mac_address (str): MAC address in format '00:11:22:33:44:55' or '001122334455'
    broadcast_ip (str, optional): Broadcast IP address. If None, defaults to '255.255.255.255'.
    port (int): Port to send the packet to (default: 9)
"""
# Clean MAC address

def send_wol(mac_address, broadcast_ip=None, port=9):
    mac_address = mac_address.replace(":", "").replace("-", "").lower()

    if len(mac_address) != 12:
        raise ValueError("Invalid MAC address format")

    # Create magic packet
    mac_bytes = bytes.fromhex(mac_address)
    magic_packet = b'\xff' * 6 + mac_bytes * 16

    # Create socket and send
    if broadcast_ip is None:
        broadcast_ip = '255.255.255.255'

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast_ip, port))

    print(f"Magic packet sent to {mac_address.upper()} via {broadcast_ip}:{port}")

# Predefined messages
cmd_ch_down = {
    "id": generate_8_digit_integer(),
    "command": "CH_DOWN",
    "description": "Simple channel down.",
}

cmd_ch_up = {
    "id": generate_8_digit_integer(),
    "command": "CH_UP",
    "description": "Simple channel up.",
}

cmd_force_ch_switch = {
    "id": generate_8_digit_integer(),
    "command": "FORCE_CH_SWITCH",
    "description": "Forces a channel switch to a given service.",
    "payload": {
        "service_id": 146,
    },
}

cmd_force_rec_event = {
    "id": generate_8_digit_integer(),
    "command": "FORCE_RECORD_EVENT",
    "description": "Forces a recording within a specified time period for a given service.",
    "payload": {
        "service_id": 4432,
        "record_start": get_start_rec_time(),
        "record_stop": get_stop_rec_time(),
    },
}

cmd_start_ch_play_with_duration = {
    "id": generate_8_digit_integer(),
    "command": "START_PLAYBACK",
    "description": "Starts playback of a given service for a specified time period.",
    "trigger_time": get_trigger_time(),
    "payload": {"service_id": 17037, "duration": 60},
}

cmd_block_ch_playback_with_duration = {
    "id": generate_8_digit_integer(),
    "command": "BLOCK_PLAYBACK",
    "description": "Block playback of a given service for a specified time period.",
    "trigger_time": get_trigger_time(),
    "payload": {"service_id": 17037, "duration": 60},
}

cmd_allow_ch_playback = {
    "id": generate_8_digit_integer(),
    "command": "ALLOW_PLAYBACK",
    "description": "Allow playback of a given service immediately.",
    "payload": {"service_id": 17037},
}

cmd_delete_recording = {
    "id": generate_8_digit_integer(),
    "command": "DELETE_RECORDING",
    "description": "Deletes a recording.",
    "trigger_time": 0,
    "payload": {"recording_uuid": "9f6d45b1-0147-4048-b361-3839e65294c6"},
}

#### END OF NORMAL CMD's


#### START OF FANTHOM CMD's
cmd_get_tuner_status = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_TUNER_STATUS",
    "description": "Get current dvb-s tuner status",
}

cmd_send_button_key = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_SEND_BUTTON_KEY",
    "description": "Send KEY button press to STB",
    "payload": {"button_key": "UP"},
}

cmd_get_screenshot = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_SCREENSHOT",
    "description": "Get a screenshot from OSD only ( no VIDEO ) from the STB",
}

cmd_get_current_epg = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_CURRENT_EPG",
    "description": "Get CURRENT EPG for given service ID",
    "payload": {"service_id": 17037},
}

cmd_get_current_epg_wo_sid = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_CURRENT_EPG",
    "description": "Get CURRENT EPG for current playback",
}

cmd_get_list_epg = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_LIST_EPG",
    "description": "Get LIST EPG for given service ID",
    "payload": {"service_id": 17037},
}

cmd_epg_search = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_SEARCH_EPG",
    "description": "Search in EPG Events title list for a given text. Return array of the eventIds.",
    "payload": {"epg_title": "internet", "service_id": 17037},
}

cmd_get_recording_list = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_RECORDING_LIST",
    "description": "Get detailed list of recordings",
}

cmd_get_short_recording_list = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_SHORT_RECORDING_LIST",
    "description": "Get short list of DVR movies",
}

cmd_play_recording = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_PLAY_RECORDING",
    "description": "Play specyfic movie",
    "payload": {"recording_uuid": "1936761a-3cfd-496c-9f9a-bc5de73ce330"},
}

cmd_update_recording = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_UPDATE_RECORDING",
    "description": "Update recording if it can be removed or not",
    "payload": {"recording_uuid": "1936761a-3cfd-496c-9f9a-bc5de73ce330", "removable": True},
}

cmd_get_timer_list = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_TIMER_LIST",
    "description": "Get Schedule Timer List",
}

cmd_remove_timer = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_REMOVE_TIMER",
    "description": "Remove Timer from the timer list",
    "payload": {"eventId": 15903},
}

cmd_add_timer = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_ADD_TIMER",
    "description": "Add Timer to the timer list",
    "payload": {
        "service_id": 17037,
        "eventId": 15903,
        "recordTimer": True
    },
}

cmd_set_ch_feed_source = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_FORCE_SET_CH_SOURCE",
    "description": "Set Channel source by Manual: OTT | SAT | UDP | AUTO",
    "payload": {"mode": "SAT"},
}

cmd_get_recording_current_status = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_RECORDING_CURRENT_STATUS",
    "description": "Get information about currenty playing recording"
}

cmd_hello_stb = {
    "id": generate_8_digit_integer(),
    "command": "HELLO_DISCOVERY"
}

cmd_reboot_stb = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_REBOOT_STB",
    "description": "Reboot STB"
}

cmd_get_dvr_status = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_DVR_STATUS",
    "description": "Get information about DVR device"
}

cmd_send_dvr_button_key = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_SEND_DVR_BUTTON_KEY",
    "description": "Send KEY button press to DVR",
    "payload": {"button_key": "STOP"},
}

#### END OF FANTHOMS CMD's

def send_message(json_message):
    server_address = (device_ip, port)
    # Convert JSON message to string and encode
    combined_message = f"{device_id}:msg:{json.dumps(json_message)}"
    encoded_message = combined_message.encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        print(f"Sending message to {server_address}")
        sock.sendto(encoded_message, server_address)

        # Set a timeout for receiving the response
        sock.settimeout(5)

        # Receive and reassemble the response
        response_data = receive_large_response(sock)
        if response_data is not None:
            header_prefix = b"CMD_GET_SCREENSHOT"
            # If the response starts with the screenshot header, process it accordingly
            if response_data.startswith(header_prefix):
                save_if_screenshot(response_data)
            else:
                # Otherwise, assume it's a JSON/text response
                print(f"Received complete response ({len(response_data)} bytes)")
                try:
                    print(response_data.decode("utf-8"))
                except UnicodeDecodeError:
                    print("Received response is not valid UTF-8 text.")
        else:
            print("No complete response received.")

    except socket.timeout:
        print("No response received within the timeout period.")

    finally:
        sock.close()

def receive_large_response(sock):
    """
    Receives and reassembles a large UDP response split into multiple packets.
    Each packet is expected to have a header (in ASCII) followed by binary data.
    The header format is assumed to be "seq/total:" where seq and total are integers.
    """
    received_chunks = {}
    expected_packets = None

    while True:
        try:
            packet, addr = sock.recvfrom(65536)  # receive raw bytes
            # Check for the special END packet
            if packet == b"END":
                print("Received END packet. Reassembling response...")
                break

            # Find the separator (colon) between header and data
            sep_index = packet.find(b":")
            if sep_index == -1:
                print(f"Invalid packet format (missing ':'): {packet}")
                continue

            # Extract and decode header
            header_bytes = packet[:sep_index]
            try:
                header = header_bytes.decode("utf-8")
            except UnicodeDecodeError:
                print("Failed to decode header")
                continue

            # Header should be in the format "seq/total"
            if "/" not in header:
                print(f"Malformed header: {header}")
                continue

            parts = header.split("/")
            if len(parts) != 2:
                print(f"Invalid header parts: {header}")
                continue

            try:
                seq_num = int(parts[0])
                total_packets = int(parts[1])
            except ValueError:
                print(f"Invalid header values: {header}")
                continue

            expected_packets = total_packets
            # The rest of the packet is the binary chunk.
            chunk = packet[sep_index + 1:]
            received_chunks[seq_num] = chunk

            # If we have received all expected packets, we can break.
            if len(received_chunks) == expected_packets:
                print("All packets received. Reassembling response...")
                break

        except socket.timeout:
            print("Socket timeout while receiving packets.")
            break

    if expected_packets is None or len(received_chunks) != expected_packets:
        print("Error: Some packets are missing!")
        return None

    # Reassemble the full response in order of packet sequence
    full_response = b"".join(received_chunks[i] for i in sorted(received_chunks.keys()))
    return full_response

def save_if_screenshot(full_response):
    """
    If full_response starts with 'CMD_GET_SCREENSHOT', then the data is expected to be
    structured as: HEADER + [BMP bytes] + ENDER + [JSON data].

    This function:
      - Extracts the BMP data between the header and the end marker.
      - Extracts the JSON data after the end marker.
      - Reads the "file_name" field from the JSON's "details" section, if available.
      - Saves the BMP data to that file in the output_dir.
      - Prints the JSON data.
    If the header is not found, it simply prints the decoded JSON.
    """
    header_prefix = b"CMD_GET_SCREENSHOT"
    ender_marker = b"CMD_GET_SCREENSHOT_END"

    if full_response.startswith(header_prefix):
        # Remove header from beginning
        remainder = full_response[len(header_prefix):]
        ender_index = remainder.find(ender_marker)
        if ender_index == -1:
            print("End marker not found in response!")
            return

        # Extract screenshot BMP data and JSON part
        screenshot_data = remainder[:ender_index]
        json_data = remainder[ender_index + len(ender_marker):]

        try:
            json_str = json_data.decode("utf-8")
            json_obj = json.loads(json_str)
        except Exception as e:
            print("Error decoding JSON data:", e)
            return

        # Use the file_name from JSON details if present, otherwise default.
        file_name = "screenshot.bmp"
        if "details" in json_obj and "file_name" in json_obj["details"]:
            file_name = json_obj["details"]["file_name"]

        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(screenshot_data)
        print(f"Screenshot saved as {file_path}")

        print("Received JSON data:")
        print(json.dumps(json_obj, indent=2))
    else:
        # If the response does not have the screenshot header, try printing it as JSON.
        try:
            json_str = full_response.decode("utf-8")
            print("Received JSON data:")
            print(json_str)
        except Exception as e:
            print("Error decoding response as JSON:", e)

# Message dictionary to choose from
message_options = {
    1: cmd_ch_down,
    2: cmd_ch_up,
    3: cmd_force_ch_switch,
    4: cmd_force_rec_event,
    5: cmd_start_ch_play_with_duration,
    6: cmd_block_ch_playback_with_duration,
    7: cmd_delete_recording,
    8: cmd_set_ch_feed_source,
    9: cmd_get_screenshot,
    10: cmd_get_recording_current_status,
    11: cmd_get_recording_list,
    12: cmd_get_tuner_status,
    13: cmd_send_button_key,
    14: cmd_get_short_recording_list,
    15: cmd_play_recording,
    16: cmd_get_current_epg,
    17: cmd_get_timer_list,
    18: cmd_remove_timer,
    19: cmd_add_timer,
    20: cmd_update_recording,
    21: cmd_epg_search,
    22: cmd_get_list_epg,
    23: cmd_get_current_epg_wo_sid,
    24: cmd_allow_ch_playback,
    25: cmd_hello_stb,
    26: cmd_reboot_stb,
    27: cmd_get_dvr_status,
    28: cmd_send_dvr_button_key
}


def main():
    # ANSI color codes
    RESET = "\033[0m"
    BLUE = "\033[94m"    # Header
    RED = "\033[91m"     # [NOT READY] or error
    BOLD = "\033[1m"

    # Category-specific colors
    DVR_COLOR = "\033[92m"   # Green
    TOOL_COLOR = "\033[93m"  # Yellow
    DVB_COLOR = "\033[96m"   # Cyan
    EPG_COLOR = "\033[95m"   # Magenta

    # Header
    print(f"{BLUE}{'='*60}")
    print(f"{BOLD}      ðŸš€ Welcome to the Command Control Tool by TiViCon ðŸš€{RESET}")
    print(f"{BLUE}{'='*60}")
    print(f"{BOLD}      Created by TiViCon Co Ltd.{RESET}")
    print(f"      ðŸŒ https://www.tivicon.com")
    print(f"      âœ‰ï¸  info@tivicon.com")
    print(f"      Â© 2024 - 2025. All rights reserved.")
    print(f"{BLUE}{'='*60}{RESET}\n")

    print("ðŸ“Œ Choose a command to send:\n")

    options = [
        (0, "[TOOL] SEND Wake-On-Lan package"),
        (1, "[DVB] CH_DOWN"),
        (2, "[DVB] CH_UP"),
        (3, "[DVB] FORCE CHANNEL SWITCH"),
        (4, "[DVB] FORCE RECORD EVENT"),
        (5, "[DVB] START PLAYBACK"),
        (6, "[DVB] BLOCK PLAYBACK for Service ID"),
        (7, "[DVR] DELETE RECORDING"),
        (8, "[TOOL] FORCE SET CH SOURCE"),
        (9, "[TOOL] GET SCREENSHOT"),
        (10, "[DVR] GET RECORDING CURRENT PLAYBACK STATUS"),
        (11, "[DVR] GET RECORDING LIST"),
        (12, "[DVB] GET TUNER STATUS"),
        (13, "[TOOL] SEND BUTTON PRESS"),
        (14, "[DVR] GET SHORT RECORDING LIST"),
        (15, "[DVR] PLAY RECORDING"),
        (16, "[EPG] GET CURRENT EPG for Service ID"),
        (17, "[EPG] GET TIMER LIST"),
        (18, "[EPG] REMOVE TIMER"),
        (19, "[EPG] ADD TIMER"),
        (20, "[TOOL] UPDATE MOVIE 'protection' flag"),
        (21, "[EPG] SEARCH EPG FOR TITLE for Service ID"),
        (22, "[EPG] GET LIST EPG"),
        (23, "[EPG] GET CURRENT EPG (current playing)"),
        (24, "[DVB] ALLOW PLAYBACK FOR for Service ID"),
        (25, "[TOOL] HELLO DISCOVERY"),
        (26, "[TOOL] REBOOT STB"),
        (27, "[DVR] GET DVR STORAGE DEVICE STATUS"),
        (28, "[TOOL] SEND DVR BUTTON PRESS"),
    ]

    # Print commands with category colors
    for num, cmd in options:
        if "[DVR]" in cmd:
            color = DVR_COLOR
        elif "[TOOL]" in cmd:
            color = TOOL_COLOR
        elif "[DVB]" in cmd:
            color = DVB_COLOR
        elif "[EPG]" in cmd:
            color = EPG_COLOR
        else:
            color = RESET

        if "[NOT READY]" in cmd:
            print(f"{RED}âŒ {num:<4}\t{cmd}{RESET}")
        else:
            print(f"{color}âœ… {num:<4}\t{cmd}{RESET}")

    try:
        choice = int(input("\n\nEnter the number of the command to send (0-28): "))
        if choice == 0:
            send_wol(device_mac)
        elif choice in message_options:
            selected_message = message_options[choice]
            send_message(selected_message)
        else:
            print(f"{RED}Invalid choice. Please select a number between 0 and 28.{RESET}")
    except ValueError:
        print(f"{RED}Invalid input. Please enter a valid number.{RESET}")


if __name__ == "__main__":
    main()