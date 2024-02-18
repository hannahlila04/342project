import cv2
from datetime import datetime


def record_video(output_file='output.mp4', frames_per_second=20.0, resolution=(640, 480), record_time=3):


    # Define the codec and create VideoWriter object
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, frames_per_second, resolution)

    # Open default webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Set resolution
    cap.set(3, resolution[0])
    cap.set(4, resolution[1])

    # Record video for a specified time
    import time
    start_time = time.time()
    while int(time.time() - start_time) < record_time:
        ret, frame = cap.read()
        if ret:
            # Write the frame to the file
            out.write(frame)

            # Display the resulting frame
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
                break
        else:
            break

    # Release everything
    cap.release()
    out.release()
    cv2.destroyAllWindows()

# Record a 10-second video
current_time = datetime.now()
time_str = current_time.strftime('%Y-%m-%d_%H-%M-%S')
unique_filename = f"dance_recording_{time_str}.mp4"

record_video(output_file=unique_filename, record_time=3)
