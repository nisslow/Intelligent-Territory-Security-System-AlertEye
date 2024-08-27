import threading
from ultralytics import YOLO
import cv2
import supervision as sv
import numpy as np
import time
import pygame
from threading import Thread
from collections import deque
from datetime import datetime, timedelta
import TelegramBot
from TelegramBot import start_telebot
import torch

width = 960
height = 500
photos_dir = "your path where to save made photos"
videos_dir = "your path where to save made videos"
path_alarm = 'your path of the alarm sound'
our_camera_stream = 'RTSP link'
camera_stream = 'RTSP link'
video_path = 'video link' # Any video on which you can test the system
global is_running
is_running = True
fourcc = cv2.VideoWriter_fourcc(*'MP4V')

points_dict = {} 
count_video, count_photo = 0, 0

"""
This function is recording video from RTSP using created buffer.
The video frame rate is recorded based on system performance and calculated in 'delay_buffer'.
By changing the 'duration', you can change the duration of the recorded video.
"""
def record_video(frame_buffer, time_buffer, delay_buffer, count_video, videos_dir, width, height): 
    frame_size = (width, height)
    time_now = datetime.now().strftime('%Y_%m_%d_%Hh%Mm%Ss')
    avg_delay = sum(delay_buffer) / len(delay_buffer)
    fps_new = int(1 / avg_delay)
    print('FPS:', fps_new)
    out = cv2.VideoWriter(f'{videos_dir}/{time_now}_output{count_video}.mp4', fourcc, fps_new, frame_size)
    print(f'{time_now}_output{count_video}.mp4')

    duration = 15
    num_frames = int(fps_new * duration)
    frame_interval = 1.0 / fps_new

    start_time = time_buffer[0]
    current_time = start_time

    for i in range(num_frames):
        if frame_buffer:
            while time_buffer and (time_buffer[0] < current_time):
                frame_buffer.popleft()
                time_buffer.popleft()

            if frame_buffer:
                frame = frame_buffer[0]
                out.write(frame)

        current_time += timedelta(seconds=frame_interval)
        time.sleep(frame_interval)

    out.release()
    print(f"Запись видео {count_video} завершена")

# This function allows you to draw lines on the every camera stream and delete all points
def draw_polygon(event, x, y, flags, param):
    file_index = param
    if event == cv2.EVENT_LBUTTONUP:
        if file_index in points_dict:
            points_dict[file_index].append((x, y))
        else:
            points_dict[file_index] = [(x, y)]
    elif event == cv2.EVENT_RBUTTONUP:
        if file_index in points_dict:
            points_dict[file_index].clear()

# Main function
def vision(stream, model, imgsz, width, height, file_index, photos_dir, videos_dir):
    # torch.cuda.set_device(0)
    torch.cuda.empty_cache()
    in_zone = False
    was_in_zone = False
    is_recording = False
    last_detected_time_sound = 0.0
    first_detected_time_object = 0.0
    last_recording_time = 0.0
    last_photo_time = 0.0
    initialized = False
    frame_buffer = deque()
    time_buffer = deque()
    delay_buffer = deque()
    # tracker = sv.ByteTrack()
    global count_video, count_photo
    # classes_to_detect = [0, 2, 7]

    pygame.init()
    pygame.mixer.music.load(path_alarm)

    results = model.track(
        source=stream,
        stream=True,
        imgsz=imgsz,
        agnostic_nms=True,
        classes=[0, 1, 2, 3, 7, 14, 16],
        conf=0.22,
        persist=True, tracker="D:\\PycharmProjects\\pythonProject19(WORK)\\bytetrack.yaml"
    )  # classes = [0, 2, 7,14,16]

    window_name = f'CAMERA{file_index}'
    cv2.namedWindow(window_name)
    cv2.resizeWindow(window_name, width, height)
    cv2.setMouseCallback(f'CAMERA{file_index}', draw_polygon, file_index)

    label_annotator = sv.LabelAnnotator(
        text_scale=0.3,
        text_padding=3,
    )
    color_annotator = sv.BoxCornerAnnotator(
        thickness=2
    )

    # system_is_on_message()              # Telegram alerts that the system is up and running
    for result in results:
        if not is_running:
            break
        frame = result.orig_img
        if not initialized:
            orig_height, orig_width = frame.shape[:2]
            print(orig_width, orig_height)
            initialized = True

        delay_buffer.append(((result.speed.get('preprocess') + result.speed.get('inference') + result.speed.get(
            'postprocess')) / 1000.0))
        frame = cv2.resize(frame, (width, height))  
        frame_buffer.append(frame.copy())
        time_buffer.append(datetime.now())
        detections = sv.Detections.from_ultralytics(result)
        detections = detections[np.isin(detections.class_id,[0, 1, 2, 3, 7])]

        while time_buffer and (datetime.now() - time_buffer[0]).total_seconds() > 15:     # Duration of the recorded video
            frame_buffer.popleft()
            time_buffer.popleft()
            delay_buffer.popleft()

        detections.xyxy[:, 0] = detections.xyxy[:, 0] * (width / orig_width)
        detections.xyxy[:, 2] = detections.xyxy[:, 2] * (width / orig_width)
        detections.xyxy[:, 1] = detections.xyxy[:, 1] * (height / orig_height)
        detections.xyxy[:, 3] = detections.xyxy[:, 3] * (height / orig_height)

        # detections = tracker.update_with_detections(detections=detections)         

        labels = [f"{result.names[class_id]}: {confidence:.2f}"
                  for class_id, confidence
                  in zip(detections.class_id, detections.confidence)]

        annotated_img = color_annotator.annotate(scene=frame.copy(), detections=detections)
        annotated_img = label_annotator.annotate(scene=annotated_img, detections=detections, labels=labels)

        if file_index in points_dict and len(points_dict[file_index]) >= 1:
            zone_polygon = np.array(points_dict[file_index], dtype=np.int32)

            zone = sv.PolygonZone(
                polygon=zone_polygon,
                triggering_anchors=(sv.Position.CENTER,)
            )

            zone_annotator = sv.PolygonZoneAnnotator(
                zone=zone,
                color=sv.Color.GREEN,
                thickness=2
            )

            trigger = zone.trigger(detections=detections)

            if trigger.any():
                if last_photo_time is None or time.time() - last_photo_time >= 20:
                    time_now = datetime.now().strftime('%Y_%m_%d_%Hh%Mm%Ss')
                    photo = f'{photos_dir}/{time_now}_photo_{str(count_photo)}.jpg'
                    cv2.imwrite(photo, annotated_img)
                    Thread(target=TelegramBot.send_new_photos, args=(photo,)).start()
                    last_photo_time = time.time()
                    count_photo += 1
                if not in_zone:
                    in_zone = True
                    if not was_in_zone:
                        first_detected_time_object = time.time()
                        was_in_zone = True
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play()
                last_detected_time_sound = time.time()
            else:
                if last_detected_time_sound and time.time() - last_detected_time_sound >= 2:
                    pygame.mixer.music.stop()
                if in_zone:
                    in_zone = False
                    is_recording = False
            if was_in_zone and first_detected_time_object and time.time() - first_detected_time_object >= 8 and not is_recording:
                first_detected_time_object = 0.0
                was_in_zone = False
                if last_recording_time is None or time.time() - last_recording_time >= 60:
                    Thread(target=record_video, args=(
                    frame_buffer.copy(), time_buffer.copy(), delay_buffer.copy(), count_video, videos_dir, width,
                    height)).start()
                    is_recording = True
                    count_video += 1
                    last_recording_time = time.time()

            annotated_img = zone_annotator.annotate(scene=annotated_img)

        cv2.imshow(f'CAMERA{file_index}', annotated_img)

        if cv2.waitKey(30) == 27:
            torch.cuda.empty_cache()
            break

    # system_is_of_message()             # Telegram alerts that the system is turned off
    cv2.destroyAllWindows()


def main():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Torch is available: {torch.cuda.is_available()}')
    print(f'Using device: {device}')
    
    models = [YOLO('path to model').to(device),
              YOLO('path to model').to(device),
              YOLO('path to model').to(device),
              ]

    streams = [
        "RTSP link",
        'RTSP link',
        'RTSP link',
    ]

    imgszs = [
        1024,
        704,
        1024,
    ]
    
    threads = [
        threading.Thread(target=vision, args=(streams[i], models[i], imgszs[i], width, height, i+1, photos_dir, videos_dir), daemon=True)
        for i in range(len(streams))
    ]
    threads.append(threading.Thread(target=start_telebot, daemon=True))

    for thread in threads:
        thread.start()
        time.sleep(0.5)

    for thread in threads:
        thread.join()

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
