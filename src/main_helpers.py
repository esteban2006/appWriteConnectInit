

import random
import string
import json
import hashlib
import sys

import os
import platform
import uuid
import hashlib
import subprocess

from pprint import pprint
from collections import OrderedDict
from typing import Union


def print_centered_banner(text, border_char='#', total_width=80):
    # Calculate how much space we have between the '##' on each side
    inner_width = total_width - 4  # 2 chars for each side

    # Center the text in the available space
    centered_text = text.center(inner_width)

    # Create the border line
    border_line = border_char * total_width

    # Build the full banner using one string
    banner = (
        f"{border_line}\n"
        f"##{centered_text}##\n"
        f"{border_line}"
    )

    print(banner)


def print_d(data):
    if not isinstance(data, dict):
        print(
            f"[WARNING] Expected dict, got {type(data).__name__}. Skipping print.")
        return

    # Get max key length
    max_key_len = max(len(str(key)) for key in data)

    # Format each line with consistent alignment
    lines = [
        f"{str(key).ljust(max_key_len)}:   {value}" for key, value in data.items()
    ]

    # Create border based on longest line
    longest_line = max(len(line) for line in lines)
    border = "=" * longest_line

    # Build banner (no leading spaces!)
    banner = f"{border}\n" \
        f"{chr(10).join(lines)}\n" \
        f"{border}"

    print(banner)


def get_magic_number(magic_len=None):
    """
    Generate a random magic number using digits only.

    Args:
        magic_len (optional): Desired length of the magic number.
                            If invalid or < 1, defaults to 9 digits.

    Returns:
        int: A randomly generated magic number.
    """
    try:
        magic_len = int(magic_len)
        if magic_len < 1:
            magic_len = 9
    except (TypeError, ValueError):
        magic_len = 9

    return int("".join(random.SystemRandom().choice(string.digits)for _ in range(magic_len)))


def oneDict(d, priority_keys=None):
    if priority_keys is None:
        priority_keys = []

    result = {}

    def _flatten(d_dict):
        for k, v in d_dict.items():
            if isinstance(v, dict):
                _flatten(v)
            else:
                result[k] = v

    _flatten(d)

    # print("Flattened dict:", result)
    # print("Priority keys:", priority_keys)

    # Build sort key map
    priority_map = {key: idx for idx, key in enumerate(priority_keys)}

    def sort_key(item):
        key = item[0]
        if key in priority_map:
            return (0, priority_map[key])  # Keep specified order
        return (1, key)  # Alphabetical for others

    # Sort items
    sorted_items = sorted(result.items(), key=sort_key)

    # Return a regular dict with insertion order preserved (Python 3.7+)
    return dict(sorted_items)


def get_hash(text, L=6):
    h = int.from_bytes(hashlib.md5(text.encode()).digest(), 'big')
    c = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    b = len(c)
    r = ''
    while h > 0 and len(r) < L:
        h, m = divmod(h, b)
        r = c[m] + r
    return r.ljust(L, c[0])

def calculate_volume(
    action: str,
    last_action: str,
    buy_vol: Union[int, float],
    sell_vol: Union[int, float],
    lot_size: Union[int, float],
    side: str
) -> float:
    """
    Calculates the volume to trade based on current and previous actions.

    Args:
        action (str): Current action ("buy" or "sell")
        last_action (str): Last executed action ("BUY" or "SELL")
        buy_vol (Union[int, float]): Total volume of buy orders so far
        sell_vol (Union[int, float]): Total volume of sell orders so far
        lot_size (Union[int, float]): Base lot size for new order
        side (str): Trading side (e.g., 'long', 'short')

    Returns:
        float: Calculated volume to trade
    """

    print_d({
        "name": "CALCULATING VOLUME / DATA RECEIVED",
        "action": action,
        "last_action": last_action,
        "buy_vol": buy_vol,
        "sell_vol": sell_vol,
        "lot_size": lot_size,
        "side": side
    })

    # Validate last_action
    if last_action not in ["SELL", "BUY"]:
        print_d({"name": "INVALID LAST ACTION — RETURNING LOT SIZE"})
        return float(lot_size)

    # Convert to float safely
    try:
        buy_vol = float(buy_vol)
        sell_vol = float(sell_vol)
        lot_size = float(lot_size)
    except (ValueError, TypeError):
        print_d({"name": "ERROR: Invalid volume value",
                 "buy_vol": buy_vol, "sell_vol": sell_vol})
        return float(lot_size)

    # Normalize case for comparison
    action = action.upper()
    last_action = last_action.upper()

    # Determine volume
    if action != last_action:
        calculated = abs(buy_vol - sell_vol) + lot_size
        print_d({
            "name": "ACTION CHANGED — RETURNING ADJUSTED VOLUME",
            "calculated_volume": calculated
        })
    else:
        calculated = lot_size
        print_d({
            "name": "SAME ACTION — RETURNING BASE LOT SIZE",
            "calculated_volume": calculated
        })

    return float(calculated)



def get_device_number():
    try:
        # Get MAC address
        mac = str(uuid.getnode())

        # Get username
        username = os.getenv("USERNAME") or os.getenv("USER") or "unknown"

        # Get disk serial (platform-dependent)
        disk_serial = "unknown"
        system = platform.system().lower()

        if "windows" in system:
            try:
                output = subprocess.check_output(
                    "wmic diskdrive get serialnumber", shell=True
                ).decode(errors="ignore").split()
                if len(output) > 1:
                    disk_serial = output[1]
            except Exception:
                pass
        elif "linux" in system:
            try:
                output = subprocess.check_output(
                    "udevadm info --query=all --name=/dev/sda | grep ID_SERIAL_SHORT",
                    shell=True,
                ).decode(errors="ignore")
                disk_serial = output.split("=")[-1].strip()
            except Exception:
                pass
        elif "darwin" in system:  # macOS
            try:
                output = subprocess.check_output(
                    "system_profiler SPStorageDataType | grep 'Serial Number'",
                    shell=True,
                ).decode(errors="ignore")
                disk_serial = output.split(":")[-1].strip()
            except Exception:
                pass

        # Combine info for stable unique key
        raw_id = f"{mac}-{username}-{disk_serial}"

        # Hash and reduce to 8 digits
        hash_object = hashlib.sha256(raw_id.encode())
        unique_number = int(hash_object.hexdigest(), 16) % 100000000

        return f"{unique_number:08d}"

    except Exception:
        # Fallback if something fails
        return "00000000"



if __name__ == "__main__":
    # Your input dict
    data = {
        "symbol": "Step Index",
        "trading_time": "2m",
        "chart_type": "candle",
        "last_action": "SELL",
        "renko_step": 1,
        "target": 3,
        "price_difference": 1,
        "lot_size": 0.1,
        "trading": [1, 2, 3, 4]
    }
    # print_d(data)
    # print (get_magic_number())
    # print(oneDict(data, ['trading']))
    # print (get_hash("esteban gilberto gutierrez jandres"))
    # calculate_volume("sell", 'BUY', 0.1, 0.2, 0.1, 'sell')
    # print_centered_banner("exiting accumulative grid trading is True", "+")
    print(get_device_number())
