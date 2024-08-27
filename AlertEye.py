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
# from TelegramBot import send_new_photos, system_is_on_message, system_is_of_message
import torch


is_running = True
our_camera_stream = ""
width = 0
height = 0
yolo_model = ''
img_size = 0
videos_dir = ""
photos_dir = ""

path_alarm = 'D:/PycharmProjects/pythonProject19(WORK)/zvuk-signala-dyimoulovitelya-pojarnaya-trevoga-40205.mp3'

camera_stream = 'rtsp://admin:admin123@192.168.1.15:554/avstream/channel=1/stream=0.sdp'
video_path = 'C:/Users/quinki/Desktop/VID_20240408_124223.mp4'
fourcc = cv2.VideoWriter_fourcc(*'MP4V')
# fps = 10

##
# frame_size = (width, height)


points = []

def stop_processes():
    torch.cuda.empty_cache()
    TelegramBot.system_is_of_message()
    global is_running
    is_running = False


def record_video(frame_buffer, time_buffer, delay_buffer, count_video, videos_dir, width, height):
    frame_size = (width, height)
    time_now = datetime.now().strftime('%Y_%m_%d_%Hh%Mm%Ss')
    avg_delay = sum(delay_buffer) / len(delay_buffer)
    fps_new = int(1 / avg_delay)
    print('FPS:', fps_new)
    out = cv2.VideoWriter(f'{videos_dir}/{time_now}_output{count_video}.mp4', fourcc, fps_new, frame_size)
    print(f'{time_now}_output{count_video}.mp4')

    duration = 10  # duration of the video in seconds
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


def draw_polygon(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONUP:
        points.append((x, y))
    elif event == cv2.EVENT_RBUTTONUP:
        points.clear()


def vision(stream_url, width, height, model_path, img_size, photos_dir, videos_dir, app ):
    # torch.cuda.set_device(0)
    torch.cuda.empty_cache()
    global is_running
    is_running = True
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Using device: {device}')
    print(torch.cuda.is_available())
    in_zone = False
    was_in_zone = False
    is_recording = False
    last_detected_time_sound = 0.0
    first_detected_time_object = 0.0
    last_recording_time = 0.0
    last_photo_time = 0.0
    count_video, count_photo = 0, 0
    frame_buffer = deque()
    time_buffer = deque()
    delay_buffer = deque()
    # frame_buffer = deque(maxlen=int(10 * fps))
    # classes_to_detect = [0, 2, 7]
    initialized = False
    pygame.init()
    pygame.mixer.music.load(path_alarm)
    try:

        model = YOLO(model=model_path, task='detect').to(device)
        # results = model.predict(source=stream_url, stream=True, imgsz=img_size, agnostic_nms=True, classes=[0, 2, 7])  # classes = [0, 2, 7,14,16]
        results = model.track(
            source=stream_url,
            stream=True,
            persist=True,
            imgsz=img_size,
            agnostic_nms=True,
            # batch=4,
            classes=[0, 2, 5, 7],
            conf=0.21,
            tracker="bytetrack.yaml",
        )

        cv2.namedWindow("AlertEye")
        # cv2.resizeWindow('camera', 1280, 720)
        cv2.setMouseCallback("AlertEye", draw_polygon)

        label_annotator = sv.LabelAnnotator(
            text_scale=0.28,
            text_padding=2,
        )
        color_annotator = sv.BoxCornerAnnotator(
            thickness=2
        )

        # tracker = sv.ByteTrack()
        TelegramBot.system_is_on_message()
        for result in results:
            if not is_running:
                break
            frame = result.orig_img
            if not initialized:
                orig_height, orig_width = frame.shape[:2]
                print(orig_width, orig_height)
                initialized = True

            delay = (result.speed.get('preprocess') + result.speed.get('inference') + result.speed.get('postprocess'))/1000.0
            delay_buffer.append(delay)
            # print(delay)

            frame = cv2.resize(frame, (width, height))  # (int(1920/2),int(1080/2)))
            frame_buffer.append(frame.copy())
            time_buffer.append(datetime.now())
            detections = sv.Detections.from_ultralytics(result)

            while time_buffer and (datetime.now() - time_buffer[0]).total_seconds() > 10:
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

            if len(points) >= 1:
                zone_polygon = np.array(points)
                zone = sv.PolygonZone(
                    polygon=zone_polygon,
                    triggering_anchors=(sv.Position.CENTER,)
                )

                zone_annotator = sv.PolygonZoneAnnotator(
                    zone=zone,
                    color=sv.Color.GREEN,
                    thickness=2,
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
                        Thread(target=record_video, args=(frame_buffer.copy(),time_buffer.copy(), delay_buffer.copy(), count_video, videos_dir, width, height)).start()
                        is_recording = True
                        count_video += 1
                        last_recording_time = time.time()

                annotated_img = zone_annotator.annotate(scene=annotated_img)
            else:
                pygame.mixer.music.stop()

            cv2.imshow("AlertEye", annotated_img)

            if cv2.waitKey(30) == 27:
                cv2.destroyAllWindows()
                torch.cuda.empty_cache()
                break
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"Error in vision thread: {e}")
        error_message = f"Ошибка в потоке vision: {str(e)}"
        app.error_signal.emit(error_message)
        stop_processes()
        torch.cuda.empty_cache()
        # app.stop_threads_signal.emit()
        cv2.destroyAllWindows()
        # system_is_of_message()

    cv2.destroyAllWindows()



# def main():
#     # thread1 = Thread(target=vision, daemon=True)
#     # thread2 = Thread(target=start_telebot, daemon=True)
#     #
#     # thread1.start()
#     # thread2.start()
#     #
#     # thread1.join()
#     # thread2.join()
#     #
#     # cv2.destroyAllWindows()
#
#
# if __name__ == '__main__':
#     main()
