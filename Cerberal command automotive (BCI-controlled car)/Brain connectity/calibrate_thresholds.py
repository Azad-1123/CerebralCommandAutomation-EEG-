# calibrate.py
import serial
import numpy as np
from scipy import signal
import time
import json
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

def calibrate_state(ser, state_name, b_notch, a_notch, b_bandpass, a_bandpass, duration=15):
    print(f"\n👉 Be {state_name.upper()} for {duration} seconds...")
    buffer = deque(maxlen=512)
    beta_readings = []
    start_time = time.time()

    while time.time() - start_time < duration:
        try:
            raw_data = ser.readline().decode('latin-1').strip()
            if raw_data:
                eeg_value = float(raw_data)
                buffer.append(eeg_value)

                if len(buffer) == 512:
                    buffer_array = np.array(buffer)
                    processed_data = process_eeg_data(buffer_array, b_notch, a_notch, b_bandpass, a_bandpass)
                    beta_energy = calculate_beta_energy(processed_data, 512)
                    beta_readings.append(beta_energy)
                    buffer.clear()
        except Exception as e:
            print(f"Calibration Error: {e}")
            continue

    average_beta = sum(beta_readings) / len(beta_readings)
    print(f"✅ {state_name.capitalize()} Average Beta Energy: {average_beta:.6f}\n")
    return average_beta

def main():
    ser = serial.Serial('COM9', 115200, timeout=1)
    b_notch, a_notch, b_bandpass, a_bandpass = setup_filters(512)

    input("Press ENTER to start RELAXED calibration...")
    relaxed_threshold = calibrate_state(ser, "relaxed", b_notch, a_notch, b_bandpass, a_bandpass)

    input("Press ENTER to start CONCENTRATED calibration...")
    concentration_threshold = calibrate_state(ser, "concentrated", b_notch, a_notch, b_bandpass, a_bandpass)

    final_threshold = (relaxed_threshold + concentration_threshold) / 2
    print(f"\n🎯 FINAL THRESHOLD: {final_threshold:.6f}")

    thresholds = {
        "relaxed_threshold": relaxed_threshold,
        "concentration_threshold": concentration_threshold,
        "final_threshold": final_threshold
    }
    with open("thresholds.json", "w") as f:
        json.dump(thresholds, f)

    print("\n✅ Calibration completed and thresholds saved to 'thresholds.json'.")

if __name__ == '__main__':
    main()
