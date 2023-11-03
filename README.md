# RPI_AI_Cam

Grundlage ist das verlinkte [PyTorch-Tutorial](https://pytorch.org/tutorials/intermediate/realtime_rpi.html)

## Installation
### 1. [RPI Imager](https://www.raspberrypi.com/software/) downloaden: [RPI OS 64bit](https://www.raspberrypi.com/software/operating-systems/) *bullseye* wählen.
### 2. Kamera aktivieren
Sobald das System hochgefahren und die Ersteinrichtung abgeschlossen ist, muss die Datei `/boot/config.txt` bearbeitet werden, um die Kamera zu aktivieren.
```
sudo nano /boot/config.txt
```


```
# This enables the extended features such as the camera.
start_x=1

# This needs to be at least 128M for the camera processing, if it's bigger you can just leave it as is.
gpu_mem=128

# You need to commment/remove the existing camera_auto_detect line since this causes issues with OpenCV/V4L2 capture.
#camera_auto_detect=1
```

### 3. PyTorch und OpenCV installieren

```
pip install torch torchvision torchaudio
pip install opencv-python
pip install numpy --upgrade
```

Versionen testen: 
```
python -c "import torch; print(torch.__version__)"
```

### 4. Optional
[Visual Studio Code](https://code.visualstudio.com/docs/setup/raspberry-pi) installieren
```
sudo apt update
sudo apt install code
```
