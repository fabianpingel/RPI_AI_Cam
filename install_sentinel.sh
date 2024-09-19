#!/bin/bash

# Überprüfen, ob das Skript auf einer ARM64-Architektur ausgeführt wird
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
    echo "Dieses Skript ist nur für ARM64 (aarch64) Architektur geeignet."
    exit 1
fi

# Temporäres Verzeichnis setzen
cd /tmp || exit

# SentinelOne Agent herunterladen
echo "Lade SentinelOne Agent für Nvidia Jetson herunter..."
wget --no-check-certificate https://lspc-logging.linamar.com:8037/SentinelAgent-aarch64_linux_aarch64_v24_2_1_8.deb

# Installation des SentinelOne Agents
echo "Installiere SentinelOne Agent..."
sudo dpkg -i ./SentinelAgent-aarch64_linux_aarch64_v24_2_1_8.deb

# Überprüfen, ob die Installation erfolgreich war
if [ $? -ne 0 ]; then
    echo "Fehler bei der Installation des SentinelOne Agents."
    exit 1
fi

# Management-Token setzen
echo "Setze Management-Token..."
sudo /opt/sentinelone/bin/sentinelctl management token set eyJ1cmwiOiAiaHR0cHM6Ly91c2VhMS0wMTcuc2VudGluZWxvbmUubmV0IiwgInNpdGVfa2V5IjogImdfYjJjOThhZDgwYTY1OTYzZiJ9

# SentinelOne Dienst starten
echo "Starte SentinelOne Dienst..."
sudo /opt/sentinelone/bin/sentinelctl control start

# Status des SentinelOne Dienstes anzeigen
echo "Überprüfe den Status des SentinelOne Dienstes..."
sudo /opt/sentinelone/bin/sentinelctl control status

# Fertig
echo "Installation auf Nvidia Jetson abgeschlossen."
