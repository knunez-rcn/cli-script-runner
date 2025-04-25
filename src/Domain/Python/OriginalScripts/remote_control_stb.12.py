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

import socket
import os

import json
import random
import uuid
from datetime import datetime, timedelta, timezone
import base64
import gzip
from io import BytesIO
import threading

VERSION = "06.02.2025"

# Unique STB ID
# device_id = "750051317"
device_id = "750051288"

# Static IP Address of STB We are sending message
# device_ip = "192.168.2.163"
device_ip = "10.30.5.38"
# Static port - DO NOT CHANGE
port = 25671

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
        "service_id": 4432,
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
    "payload": {"service_id": 4432, "duration": 60},
}

cmd_block_ch_playback_with_duration = {
    "id": generate_8_digit_integer(),
    "command": "BLOCK_PLAYBACK",
    "description": "Block playback of a given service for a specified time period.",
    "trigger_time": get_trigger_time(),
    "payload": {"service_id": 4432, "duration": 60},
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
    "api_key": "123456abcdef",
    "command": "CMD_GET_TUNER_STATUS",
    "description": "Get current dvb-s tuner status",
}

cmd_send_button_key = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_SEND_BUTTON_KEY",
    "description": "Send KEY button press to STB",
    "payload": {"button_key": "UP"},
}

cmd_get_screenshot = {
    "id": generate_8_digit_integer(),
    "command": "CMD_GET_SCREENSHOT",
    "description": "Get a screenshot from OSD only ( no VIDEO ) from the STB",
}

cmd_get_current_epg = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_GET_CURRENT_EPG",
    "description": "Get CURRENT EPG for given service ID",
    "payload": {"service_id": 4437},
}

cmd_get_current_epg_wo_sid = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_GET_CURRENT_EPG",
    "description": "Get CURRENT EPG for current playback",
}

cmd_get_list_epg = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_GET_LIST_EPG",
    "description": "Get LIST EPG for given service ID",
    "payload": {"service_id": 4409},
}

cmd_epg_search = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_GET_SEARCH_EPG",
    "description": "Search in EPG Events title list for a given text. Return array of the eventIds.",
    "payload": {"epg_title": "internet", "service_id": 4437},
}

cmd_get_recording_list = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_GET_RECORDING_LIST",
    "description": "Get detailed list of recordings",
}

cmd_get_short_recording_list = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_GET_SHORT_RECORDING_LIST",
    "description": "Get short list of DVR movies",
}

cmd_play_recording = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_PLAY_RECORDING",
    "description": "Play specyfic movie",
    "payload": {"recording_uuid": "41e7987a-ad45-4d92-9d47-6ff2b3c21603"},
}

cmd_update_recording = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_UPDATE_RECORDING",
    "description": "Update recording if it can be removed or not",
    "payload": {"recording_uuid": "41e7987a-ad45-4d92-9d47-6ff2b3c21603", "removable": True},
}

cmd_get_timer_list = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_GET_TIMER_LIST",
    "description": "Get Schedule Timer List",
}

cmd_remove_timer = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_REMOVE_TIMER",
    "description": "Remove Timer from the timer list",
    "payload": {"eventId": 15903},
}

cmd_add_timer = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_ADD_TIMER",
    "description": "Add Timer to the timer list",
    "payload": {
        "service_id": 4409,
        "eventId": 15903,
        "recordTimer": True
    },
}
#### END OF FANTHOMS CMD's

# DOES NOT READY START
cmd_set_ch_feed_source = {
    "id": generate_8_digit_integer(),
    "command": "CMD_FORCE_SET_CH_SOURCE",
    "description": "Set Channel source by Manual: OTT | SAT | UDP | AUTO",
    "payload": {"service_id": 4432, "mode": "OTT"},
}

cmd_stb_pairing = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_PAIR_STB",
    "description": "Get pernament API Key to communicate with that STB",
    "payload": {"temp_api_key": "abcdef123456"},
}

cmd_get_dvr_current_status = {
    "id": generate_8_digit_integer(),
    "api_key": "123456abcdef",
    "command": "CMD_GET_DVR_CURRENT_STATUS",
    "description": "Get information about movie"
}
# DOES NOT READY END



def send_message(json_message):
    server_address = (device_ip, port)
    json_data = json.dumps(json_message).encode("utf-8")
    combined_message = f"{device_id}:msg:{json_message}"
    encoded_message = combined_message.encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        print(f"Sending message to {server_address}")
        sock.sendto(encoded_message, server_address)

        # Set a timeout for receiving the response
        sock.settimeout(5)

        # Buffer to receive the response
        response_data = receive_large_response(sock)

        if response_data:
            print(f"Received complete response ({len(response_data)} bytes)")
            print(response_data.decode("utf-8"))

    except socket.timeout:
        print("No response received within the timeout period.")

    finally:
        sock.close()


def receive_large_response(sock):
    """Receives and reassembles a large UDP response split into multiple packets."""
    received_chunks = {}
    expected_packets = None

    while True:
        try:
            response, server = sock.recvfrom(65536)  # Receive a chunk
            response_str = response.decode("utf-8")

            if response_str == "END":  # Check for END signal
                print("Received END packet. Reassembling response...")
                break

            # Extract sequence header (e.g., "0/5:chunk_data")
            parts = response_str.split(":", 1)
            if len(parts) < 2:
                print(f"Invalid packet format: {response_str}")
                continue

            header, chunk_data = parts
            seq_info = header.split("/")

            if len(seq_info) != 2:
                print(f"Malformed header: {header}")
                continue

            seq_num, total_packets = int(seq_info[0]), int(seq_info[1])
            expected_packets = total_packets

            # Store chunk
            received_chunks[seq_num] = chunk_data

            # If all packets received, stop
            if len(received_chunks) == expected_packets:
                print("All packets received. Reassembling response...")
                break

        except socket.timeout:
            print("Timeout while receiving packets.")
            break

    if expected_packets is None or len(received_chunks) != expected_packets:
        print("Error: Some packets are missing!")
        return None

    # Reassemble message
    sorted_chunks = [received_chunks[i] for i in sorted(received_chunks.keys())]
    full_response = "".join(sorted_chunks).encode("utf-8")
    return full_response



def sanitize_filename(filename):
    """Sanitize the received filename to remove invalid characters."""
    return filename.replace("\x00", "").strip()

def handle_client_connection(conn, addr, output_dir):
    """Handle file transfer for a single client."""
    print(f"Connected by {addr}")

    try:
        # Receive file metadata
        raw_file_name = conn.recv(1024).decode("utf-8")  # Receive raw file name
        file_name = sanitize_filename(raw_file_name)  # Sanitize the file name
        if not file_name:
            print("Error: Invalid file name received.")
            return

        file_size = int.from_bytes(conn.recv(8), byteorder='big')  # Receive file size
        print(f"Receiving file: {file_name} ({file_size} bytes)")

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Receive the file data
        received_size = 0
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "wb") as file:
            while received_size < file_size:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                file.write(chunk)
                received_size += len(chunk)

        print(f"File saved at: {file_path}")

    except Exception as e:
        print(f"Error handling client {addr}: {e}")

    finally:
        conn.close()
        print(f"Connection closed for {addr}")


def receive_file(server_ip, server_port, output_dir):
    """Start a TCP server to handle file transfers."""
    def server_thread():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((server_ip, server_port))
            server_socket.listen(5)  # Allow up to 5 simultaneous connections
            print(f"Listening for connections on {server_ip}:{server_port}...")

            while True:
                conn, addr = server_socket.accept()  # Accept a new client connection
                # Start a new thread to handle the client
                client_thread = threading.Thread(target=handle_client_connection, args=(conn, addr, output_dir))
                client_thread.daemon = True  # Allow the thread to exit when the main program exits
                client_thread.start()
                print(f"Started thread to handle client {addr}")

    # Run the server thread
    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

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
    10: cmd_stb_pairing,
    11: cmd_get_dvr_current_status,
    12: cmd_get_recording_list,
    13: cmd_get_tuner_status,
    14: cmd_send_button_key,
    15: cmd_get_short_recording_list,
    16: cmd_play_recording,
    17: cmd_get_current_epg,
    18: cmd_get_timer_list,
    19: cmd_remove_timer,
    20: cmd_add_timer,
    21: cmd_update_recording,
    22: cmd_epg_search,
    23: cmd_get_list_epg,
    24: cmd_get_current_epg_wo_sid
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
        (3, "FORCE_CH_SWITCH"),
        (4, "FORCE_RECORD_EVENT"),
        (5, "START_PLAYBACK"),
        (6, "BLOCK_PLAYBACK"),
        (7, "DELETE_RECORDING"),
        (8, "[NOT READY] FORCE SET CH SOURCE"),
        (9, "GET SCREENSHOT"),
        (10, "[NOT READY] STB PAIRING"),
        (11, "[NOT READY] GET DVR PLAYBACK STATUS"),
        (12, "GET RECORDING LIST"),
        (13, "GET TUNER STATUS"),
        (14, "SEND BUTTON PRESS"),
        (15, "GET SHORT RECORDING LIST"),
        (16, "PLAY DVR MOVIE"),
        (17, "GET CURRENT EPG for Service ID"),
        (18, "GET TIMER LIST"),
        (19, "REMOVE TIMER"),
        (20, "ADD TIMER"),
        (21, "UPDATE MOVIE 'protection' flag"),
        (22, "SEARCH EPG FOR TITLE for Service ID"),
        (23, "GET LIST EPG"),
        (24, "GET CURRENT EPG (current playing)")
    ]

    # Print commands with colored "[NOT READY]" lines
    for num, cmd in options:
        if "[NOT READY]" in cmd:
            print(f"{RED}❌ {num:<4}\t{cmd}{RESET}")
        else:
            print(f"✅ {num:<4}\t{cmd}")

    try:
        choice = int(input("\n\nEnter the number of the command to send (1-24): "))
        if choice in message_options:
            # We start reciever thread only for command 9 - CMD_GET_SCREENSHOT
            if choice == 9: receive_file(server_ip, server_port, output_dir)

            selected_message = message_options[choice]
            send_message(selected_message)
        else:
            print("Invalid choice. Please select a number between 1 and 24.")

    except ValueError:
        print("Invalid input. Please enter a valid number.")

if __name__ == "__main__":
    server_ip = "0.0.0.0"  # Bind to all interfaces
    server_port = 5000
    output_dir = "./screenshots/"  # Directory to save the received file
    main()
