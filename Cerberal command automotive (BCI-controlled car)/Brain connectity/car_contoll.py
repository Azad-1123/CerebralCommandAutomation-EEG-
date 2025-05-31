# rc_brain_control_bluetooth.py

import serial
import numpy as np
from scipy import signal
import json
import time
from collections import deque

def setup_filters(sampling_rate):
    b_notch, a_notch = signal.iirnotch(50.0 / (0.5 * sampling_rate), 30.0)
    b_bandpass, a_bandpass = signal.butter(4, [0.5 / (0.5 * sampling_rate), 30.0 / (0.5 * sampling_rate)], 'band')
    return b_notch, a_notch, b_bandpass, a_bandpass

def process_eeg_data(data, b_notch, a_notch, b_bandpass, a_bandpass):
    data = signal.filtfilt(b_notch, a_notch, data)
    data = signal.filtfilt(b_bandpass, a_bandpass, data)
    return data

def calculate_beta_energy(segment, sampling_rate):
    f, psd_values = signal.welch(segment, fs=sampling_rate, nperseg=len(segment))
    beta_band = (14, 30)
    idx = np.where((f >= beta_band[0]) & (f <= beta_band[1]))
    beta_energy = np.sum(psd_values[idx])
    return beta_energy

def main():
    with open("thresholds.json", "r") as f:
        thresholds = json.load(f)
    THRESHOLD = thresholds["final_threshold"]
    print(f"🎯 Using Threshold: {THRESHOLD:.6f}")

    eeg_ser = serial.Serial('COM9', 115200, timeout=1)
    bt_ser = serial.Serial('COM14', 9600, timeout=1)
    time.sleep(2)

    sampling_rate = 512
    b_notch, a_notch, b_bandpass, a_bandpass = setup_filters(sampling_rate)
    buffer = deque(maxlen=sampling_rate)

    moving = False
    last_beta_energy = None
    beta_high = False
    last_movement_time = 0
    MOVE_DURATION = 3.0  # seconds

    print("\n✅ Starting brain-controlled RC car...\n")

    while True:
        try:
            raw_data = eeg_ser.readline().decode('latin-1').strip()
            if raw_data:
                eeg_value = float(raw_data)
                buffer.append(eeg_value)

                if len(buffer) == sampling_rate:
                    buffer_array = np.array(buffer)
                    processed_data = process_eeg_data(buffer_array, b_notch, a_notch, b_bandpass, a_bandpass)
                    beta_energy = calculate_beta_energy(processed_data, sampling_rate)

                    if last_beta_energy is not None and abs(beta_energy - last_beta_energy) > 50:
                        print(f"⚡ Spike ignored (Current: {beta_energy:.2f}, Last: {last_beta_energy:.2f})")
                        buffer.clear()
                        continue

                    print(f"Beta Energy: {beta_energy:.6f}")
                    current_time = time.time()

                    if beta_energy > THRESHOLD and not beta_high:
                        bt_ser.write(b'F')
                        print("🚗 Moving forward (Sent 'F')")
                        last_movement_time = current_time
                        moving = True
                        beta_high = True

                    if moving and (current_time - last_movement_time >= MOVE_DURATION):
                        bt_ser.write(b'S')
                        print("🛑 Auto-stopped after move duration (Sent 'S')")
                        moving = False

                    if beta_energy < THRESHOLD:
                        beta_high = False

                    last_beta_energy = beta_energy
                    buffer.clear()

        except Exception as e:
            print(f'Error: {e}')
            continue

if __name__ == '__main__':
    main()
