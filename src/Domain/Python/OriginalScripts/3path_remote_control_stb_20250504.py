VERSION = "02.05.2025"


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


# Unique STB ID
device_id = "7500XXXX"

# Static IP Address of STB We are sending message
device_ip = "XX.XX.XX.XX"

# Static port - DO NOT CHANGE
port = 25671

# Pernament API key used for Fanthom
api_key = "dca15ceb-39c9-49f8-a0a6-a85c7402af6e"

def generate_8_digit_integer():
    return random.randint(1, 99999999)

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
	"api_key": api_key,
    "command": "FORCE_CH_SWITCH",
    "description": "Forces a channel switch to a given service.",
    "payload": {
        "service_id": 101,
    },
}

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

cmd_get_current_epg = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_CURRENT_EPG",
    "description": "Get CURRENT EPG for given service ID",
    "payload": {"service_id": 101},
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
    "payload": {"service_id": 101},
}

cmd_get_search_epg = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_GET_SEARCH_EPG",
    "description": "Search in EPG Events title list for a given text. Return array of the eventIds.",
    "payload": {"epg_title": "internet", "service_id": 101},
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
        "recordTimer": False
    },
}
    
cmd_set_ch_feed_source = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_FORCE_SET_CH_SOURCE",
    "description": "Set Channel source by Manual: OTT | SAT | UDP | AUTO",
    "payload": {"mode": "SAT"},
}

cmd_reboot_stb = {
    "id": generate_8_digit_integer(),
    "api_key": api_key,
    "command": "CMD_REBOOT_STB",
    "description": "Reboot STB"
}

cmd_hello_stb = {
    "id": generate_8_digit_integer(),
    "command": "HELLO_DISCOVERY"}



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
        sock.settimeout(10)

        # Receive and reassemble the response
        response_data = receive_large_response(sock)
        if response_data is not None:
           
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


# Message dictionary to choose from
message_options = {
    1: cmd_ch_down,
    2: cmd_ch_up,
    3: cmd_force_ch_switch,
    4: cmd_set_ch_feed_source,
    5: cmd_get_tuner_status,
    6: cmd_send_button_key,
    7: cmd_get_current_epg,
    8: cmd_get_timer_list,
    9: cmd_remove_timer,
    10: cmd_add_timer,
    11: cmd_get_search_epg,
    12: cmd_get_list_epg,
    13: cmd_get_current_epg_wo_sid,
    14: cmd_hello_stb,
	15: cmd_reboot_stb
}

            
def main():


    # Display options
    print("Choose a command to send:\n")

    options = [
        (1, "CH_DOWN"),
        (2, "CH_UP"),
        (3, "FORCE CHANNEL SWITCH"),
        (4, "FORCE SET CH SOURCE"),
        (5, "GET TUNER STATUS"),
        (6, "SEND BUTTON PRESS"),
        (7, "GET CURRENT EPG for Service ID"),
        (8, "GET TIMER LIST"),
        (9, "REMOVE TIMER"),
        (10, "ADD TIMER"),
        (11, "SEARCH EPG FOR TITLE for Service ID"),
        (12, "GET LIST EPG"),
        (13, "GET CURRENT EPG (current playing)"),
        (14, "HELLO DISCOVERY"),
		(15, "Reboot STB")
    ]

    # Print commands with colored "[NOT READY]" lines
    for num, cmd in options:
        if "[NOT READY]" in cmd:
            print(f"{RED}❌ {num:<4}\t{cmd}{RESET}")
        else:
            print(f"✅ {num:<4}\t{cmd}")

    try:
        choice = int(input("\n\nEnter the number of the command to send (1-14): "))
        if choice in message_options:
            selected_message = message_options[choice]
            send_message(selected_message)
        else:
            print("Invalid choice. Please select a number between 1 and 14.")
    
    except ValueError:
        print("Invalid input. Please enter a valid number : " + ValueError)

if __name__ == "__main__":
    main()
