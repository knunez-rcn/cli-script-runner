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

VERSION = "01.04.2025"


'''
Changes:
01.04.2025

- Add WOL command

28.03.2025

- Add Reboot Command


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

import traceback
import logging

# Unique STB ID
device_id = "750051288"

# Static IP Address of STB We are sending message
device_ip = "10.30.5.197"
# MAC Address of STB to send WOL message
device_mac = "ac:f4:2c:99:2f:51"

# Static port - DO NOT CHANGE
port = 25671

# Pernament API key used for Fanthom
api_key = "dca15ceb-39c9-49f8-a0a6-a85c7402af6e"

def setup_logging(log_dir="./../api_logs"):
    """Configure comprehensive logging for API interactions"""
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Generate timestamped log files
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = f"{log_dir}/stb_api_{timestamp}.log"
    json_log_file = f"{log_dir}/stb_api_{timestamp}.jsonl"
    raw_log_dir = f"{log_dir}/raw_{timestamp}"

    # Create raw data directory
    os.makedirs(raw_log_dir, exist_ok=True)

    # Configure logger
    logger = logging.getLogger("stb_api")
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    ))
    logger.addHandler(file_handler)

    # Console handler for info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    logger.addHandler(console_handler)

    # JSON log handler
    class JsonLogHandler(logging.FileHandler):
        def emit(self, record):
            # Only process records with our special attribute
            if hasattr(record, 'json_data'):
                with open(self.baseFilename, 'a') as f:
                    json.dump(record.json_data, f)
                    f.write('\n')

    json_handler = JsonLogHandler(json_log_file)
    logger.addHandler(json_handler)

    # Return logger and paths for later use
    return logger, raw_log_dir

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
        "service_id": 4431,
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
    "payload": {"service_id": 4431, "duration": 60},
}

cmd_block_ch_playback_with_duration = {
    "id": generate_8_digit_integer(),
    "command": "BLOCK_PLAYBACK",
    "description": "Block playback of a given service for a specified time period.",
    "trigger_time": get_trigger_time(),
    "payload": {"service_id": 4431, "duration": 60},
}

cmd_allow_ch_playback = {
    "id": generate_8_digit_integer(),
    "command": "ALLOW_PLAYBACK",
    "description": "Allow playback of a given service immediately.",
    "payload": {"service_id": 4431},
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
    "payload": {"service_id": 4431},
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
    "payload": {"service_id": 4431},
}

cmd_epg_search = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_SEARCH_EPG",
    "description": "Search in EPG Events title list for a given text. Return array of the eventIds.",
    "payload": {"epg_title": "internet", "service_id": 4431},
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
        "service_id": 4431,
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
    "command": "HELLO_DISCOVERY"}

cmd_reboot_stb = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_REBOOT_STB"}

#### END OF FANTHOMS CMD's

def send_message(json_message):
    logger, raw_log_dir = setup_logging()
    server_address = (device_ip, port)
    request_id = json_message.get('id', 'unknown')
    command = json_message.get('command', 'unknown')

    # Log the request
    logger.info(f"API Request [{request_id}]: Sending {command} to {device_ip}:{port}")

    # Save raw request
    request_file = f"{raw_log_dir}/request_{request_id}.json"
    with open(request_file, 'w') as f:
        json.dump(json_message, f, indent=2)

    # Log structured JSON
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, "", (), None
    )
    record.json_data = {
        "type": "request",
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "command": command,
        "destination": f"{device_ip}:{port}",
        "payload": json_message
    }
    logger.handle(record)

    # Encode and send message
    combined_message = f"{device_id}:msg:{json.dumps(json_message)}"
    encoded_message = combined_message.encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        logger.info(f"Sending packet ({len(encoded_message)} bytes)")
        sock.sendto(encoded_message, server_address)

        # Set timeout
        sock.settimeout(5)

        # Receive and log response
        response_data = receive_large_response(sock, logger, raw_log_dir, request_id)

        if response_data is not None:
            # Save raw response
            response_file = f"{raw_log_dir}/response_{request_id}.bin"
            with open(response_file, 'wb') as f:
                f.write(response_data)

            logger.info(f"Received complete response ({len(response_data)} bytes)")

            # Process response based on type
            if response_data.startswith(b"CMD_GET_SCREENSHOT"):
                save_if_screenshot(response_data, logger, raw_log_dir)
            else:
                try:
                    response_text = response_data.decode("utf-8")
                    logger.debug(f"Response content: {response_text}")

                    # Log structured response
                    record = logger.makeRecord(
                        logger.name, logging.INFO, "", 0, "", (), None
                    )

                    try:
                        response_json = json.loads(response_text)
                        record.json_data = {
                            "type": "response",
                            "timestamp": datetime.now().isoformat(),
                            "request_id": request_id,
                            "command": command,
                            "response_size": len(response_data),
                            "response": response_json
                        }
                    except json.JSONDecodeError:
                        record.json_data = {
                            "type": "response_text",
                            "timestamp": datetime.now().isoformat(),
                            "request_id": request_id,
                            "command": command,
                            "response_size": len(response_data),
                            "response_text": response_text
                        }

                    logger.handle(record)
                    print(response_text)

                except UnicodeDecodeError:
                    # Log binary response
                    logger.error("Response is not valid UTF-8 text")
                    record = logger.makeRecord(
                        logger.name, logging.INFO, "", 0, "", (), None
                    )
                    record.json_data = {
                        "type": "binary_response",
                        "timestamp": datetime.now().isoformat(),
                        "request_id": request_id,
                        "command": command,
                        "response_size": len(response_data),
                        "response_hex": binascii.hexlify(response_data[:200]).decode() + "..." if len(response_data) > 200 else binascii.hexlify(response_data).decode()
                    }
                    logger.handle(record)
        else:
            logger.warning("No complete response received")

    except Exception as e:
        logger.error(f"Error in communication: {str(e)}")
        logger.debug(traceback.format_exc())

        record = logger.makeRecord(
            logger.name, logging.ERROR, "", 0, "", (), None
        )
        record.json_data = {
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "command": command,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        logger.handle(record)

    finally:
        sock.close()


def receive_large_response(sock, logger=None, raw_log_dir=None, request_id=None):
    """Receives and reassembles multi-packet responses with detailed logging"""
    """
    Receives and reassembles a large UDP response split into multiple packets.
    Each packet is expected to have a header (in ASCII) followed by binary data.
    The header format is assumed to be "seq/total:" where seq and total are integers.
    """
    if logger is None:
        logger, raw_log_dir = setup_logging()

    received_chunks = {}
    expected_packets = None
    packet_counter = 0

    logger.debug("Starting to receive response packets")

    while True:
        try:
            packet, addr = sock.recvfrom(65536)
            packet_counter += 1

            # Save raw packet for debugging
            if raw_log_dir:
                packet_file = f"{raw_log_dir}/packet_{request_id}_{packet_counter}.bin"
                with open(packet_file, 'wb') as f:
                    f.write(packet)

            # Log packet info
            logger.debug(f"Received packet {packet_counter}: {len(packet)} bytes from {addr}")

            # Process packet
            if packet == b"END":
                logger.debug("Received END packet")
                break

            sep_index = packet.find(b":")
            if sep_index == -1:
                logger.warning(f"Invalid packet format (missing separator)")
                continue

            # Extract header
            try:
                header = packet[:sep_index].decode("utf-8")
                parts = header.split("/")
                seq_num = int(parts[0])
                total_packets = int(parts[1])

                expected_packets = total_packets
                chunk = packet[sep_index + 1:]
                received_chunks[seq_num] = chunk

                logger.debug(f"Processed packet {seq_num}/{total_packets}")

                if len(received_chunks) == expected_packets:
                    logger.info(f"All {expected_packets} packets received")
                    break

            except Exception as e:
                logger.warning(f"Error processing packet: {str(e)}")
                # Save problematic packet for analysis
                if raw_log_dir:
                    error_file = f"{raw_log_dir}/error_packet_{request_id}_{packet_counter}.bin"
                    with open(error_file, 'wb') as f:
                        f.write(packet)
                continue

        except socket.timeout:
            logger.warning("Socket timeout while receiving packets")
            break

    # Reassemble and return full response
    if expected_packets is None or len(received_chunks) != expected_packets:
        logger.error(f"Incomplete response: {len(received_chunks)}/{expected_packets if expected_packets else 'unknown'} packets received")
        return None

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
    26: cmd_reboot_stb
}

            
def main():
    # ANSI color codes
    RESET = "\033[0m"   # Reset to default color
    BLUE = "\033[94m"   # Blue color for the header
    RED = "\033[91m"    # Red color for [NOT READY] lines
    BOLD = "\033[1m"    # Bold text

    # Print a stylish header in blue
    print(f"{BLUE}{'='*60}")
    print(f"{BOLD}      🚀 Welcome to the Command Control Tool by TiViCon 🚀{RESET}")
    print(f"{BLUE}{'='*60}")
    print(f"{BOLD}      Created by TiViCon Co Ltd.{RESET}")
    print(f"      🌐 https://www.tivicon.com")
    print(f"      ✉️  info@tivicon.com")
    print(f"      © 2024 - 2025. All rights reserved.")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Display options
    print("📌 Choose a command to send:\n")

    options = [
        (1, "CH_DOWN"),
        (2, "CH_UP"),
        (3, "FORCE CHANNEL SWITCH"),
        (4, "FORCE RECORD EVENT"),
        (5, "START PLAYBACK"),
        (6, "BLOCK PLAYBACK for Service ID"),
        (7, "DELETE RECORDING"),
        (8, "FORCE SET CH SOURCE"),
        (9, "GET SCREENSHOT"),
        (10, "GET RECORDING CURRENT PLAYBACK STATUS"),
        (11, "GET RECORDING LIST"),
        (12, "GET TUNER STATUS"),
        (13, "SEND BUTTON PRESS"),
        (14, "GET SHORT RECORDING LIST"),
        (15, "PLAY RECORDING"),
        (16, "GET CURRENT EPG for Service ID"),
        (17, "GET TIMER LIST"),
        (18, "REMOVE TIMER"),
        (19, "ADD TIMER"),
        (20, "UPDATE MOVIE 'protection' flag"),
        (21, "SEARCH EPG FOR TITLE for Service ID"),
        (22, "GET LIST EPG"),
        (23, "GET CURRENT EPG (current playing)"),
        (24, "ALLOW PLAYBACK FOR for Service ID"),
        (25, "HELLO DISCOVERY"),
        (26, "REBOOT STB"),
        (27, "SEND Wake-On-Lan package")
    ]

    # Print commands with colored "[NOT READY]" lines
    for num, cmd in options:
        if "[NOT READY]" in cmd:
            print(f"{RED}❌ {num:<4}\t{cmd}{RESET}")
        else:
            print(f"✅ {num:<4}\t{cmd}")

    try:
        choice = int(input("\n\nEnter the number of the command to send (1-27): "))
        if choice == 27:
            send_wol(device_mac)
        else:
            if choice in message_options:
                selected_message = message_options[choice]
                send_message(selected_message)
            else:
                print("Invalid choice. Please select a number between 1 and 27.")
    
    except ValueError:
        print("Invalid input. Please enter a valid number : " + ValueError)

if __name__ == "__main__":
    output_dir = "./screenshots/"  # Directory to save the received file
    main()
