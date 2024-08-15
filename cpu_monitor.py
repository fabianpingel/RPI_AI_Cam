import os
import time
import datetime

def get_cpu_temp():
    """Liest die CPU-Temperatur aus."""
    temp = os.popen("vcgencmd measure_temp").readline()
    return float(temp.replace("temp=", "").replace("'C\n", ""))

def get_cpu_freq():
    """Liest die CPU-Taktfrequenz aus."""
    freq = os.popen("vcgencmd measure_clock arm").readline()
    return int(freq.replace("frequency(48)=", "").strip())

def log_data(filename, interval=60):
    """Protokolliert die CPU-Temperatur und -Taktfrequenz in eine Datei."""
    with open(filename, 'a') as file:
        while True:
            # Hole aktuelle Zeit
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Hole CPU-Daten
            cpu_temp = get_cpu_temp()
            cpu_freq = get_cpu_freq() / 1_000_000  # Frequenz in MHz
            
            # Log-Eintrag
            log_entry = f"{timestamp}, Temp: {cpu_temp}°C, Freq: {cpu_freq} MHz\n"
            print(log_entry.strip())
            file.write(log_entry)
            
            # Warte das definierte Intervall
            time.sleep(interval)

if __name__ == "__main__":
    log_data("cpu_log.txt", interval=60)  # Intervall auf 60 Sekunden setzen
