import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import cv2
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import numpy as np
from kalman_filter import Kalman_Filtering

MARGIN = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green

def draw_landmarks_on_image(rgb_image, detection_result):
  hand_landmarks_list = detection_result.hand_landmarks
  handedness_list = detection_result.handedness
  annotated_image = np.copy(rgb_image)

  # Loop through the detected hands to visualize.
  for idx in range(len(hand_landmarks_list)):
    hand_landmarks = hand_landmarks_list[idx]
    handedness = handedness_list[idx]

    # Draw the hand landmarks.
    hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    hand_landmarks_proto.landmark.extend([
      landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
    ])
    solutions.drawing_utils.draw_landmarks(
      annotated_image,
      hand_landmarks_proto,
      solutions.hands.HAND_CONNECTIONS,
      solutions.drawing_styles.get_default_hand_landmarks_style(),
      solutions.drawing_styles.get_default_hand_connections_style())

    # Get the top left corner of the detected hand's bounding box.
    height, width, _ = annotated_image.shape
    x_coordinates = [landmark.x for landmark in hand_landmarks]
    y_coordinates = [landmark.y for landmark in hand_landmarks]
    text_x = int(min(x_coordinates) * width)
    text_y = int(min(y_coordinates) * height) - MARGIN

    # Draw handedness (left or right hand) on the image.
    cv2.putText(annotated_image, f"{handedness[0].category_name}",
                (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)

  return annotated_image

def main():
    base_options = mp_python.BaseOptions(model_asset_path="models/hand_landmarker.task")
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        running_mode=vision.RunningMode.IMAGE,
    )
    detector = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0)

    # Pobierz wymiary obrazu
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Utwórz 21 instancji filtra Kalmana, po jednej dla każdego punktu dłoni
    kalman_filters = []
    for i in range(21):
        kf = Kalman_Filtering(n_points=1)
        kf.initialize()
        kalman_filters.append(kf)


    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Nie można odczytać z kamery")
            break
        
        # Konwertuj BGR (OpenCV) do RGB (MediaPipe)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Utwórz obiekt MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Detekcja dłoni
        result = detector.detect(mp_image)
        
        # Rysuj punkty na frame'ie
        if result.hand_landmarks:
            
            # Utwórz nową listę wygładzonych landmarków
            smoothed_landmarks = []

            for idx in range(len(result.hand_landmarks[0])):
                  landmark = result.hand_landmarks[0][idx]

                  point = np.array([landmark.x*width, landmark.y*height], np.float32)
                  print(point)

                  # Przepuść przez filtr Kalmana
                  smoothed = kalman_filters[idx].predict(point)
                  # Konwertuj z powrotem na znormalizowane współrzędne
                  smoothed_x = smoothed[0] / width
                  smoothed_y = smoothed[1] / height

                  smoothed_landmark = type(landmark)(x=float(smoothed_x), y=float(smoothed_y), z=landmark.z)
                  smoothed_landmarks.append(smoothed_landmark)
            
            # Zastąp oryginalne landmarki wygładzonymi
            result.hand_landmarks[0] = smoothed_landmarks              

            frame = draw_landmarks_on_image(frame, result)
        
        # Wyświetl obraz
        cv2.imshow('Hand Tracking', frame)
        
        # Wyjdź po naciśnięciu 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Zwolnij zasoby
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()