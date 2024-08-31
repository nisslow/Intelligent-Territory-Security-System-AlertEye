# Intelligent-Territory-Security-System
It has two version of it:
First - MainApp and AlertEye is one version of the code. In this one you have GUI with some customizable settings.
Second - Multiple cameras - this version can handle multiple cameras, but it doesn't have GUI.

# Video surveillance system with AI object detection

This system is a complete video surveillance solution using artificial intelligence to detect and classify objects in real time.

## Main Functions

- Continuous monitoring of the enterprise territory in real time
- Object localization and classification (people, vehicles, etc.)
- Generation of sound alerts when objects are detected in a specified area
- Automatic saving of video and photos when violations are detected
- Sending photo frames of violations via Telegram-bot
- Customizable detection zones for each video stream
- Graphical interface for system management

## Features

- Simultaneous processing of multiple video streams from different cameras
- Optimization for both CPU and GPU for better performance
- Utilizes state-of-the-art computer vision models (YOLO)
- Multi-threaded architecture for efficient data processing

## Technologies

- Python
- OpenCV
- PyTorch
- Ultralytics YOLO
- Supervision
- Pygame (for sound notifications)
- Telegram API (for sending notifications)

## Configuration
- Install all libraries (Download through terminal in project Pytorch with CUDA fron official web site : https://pytorch.org/get-started/locally/)
- Configure the directory paths for saving photos and videos in the `photos_dir` and `videos_dir` variables
- Specify the RTSP streams of the cameras in the `streams` list
- Download any YOLO family models from the official source. If necessary, change YOLO models or their parameters in the `models` list
