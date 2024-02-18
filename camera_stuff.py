import cv2
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os.path

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


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


def upload_video(filename):
    current_time = datetime.now()
    time_str = current_time.strftime('%Y-%m-%d_%H-%M-%S')
    unique_filename = f"dance_recording_{time_str}.mp4"


    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
    file_metadata = {'name': filename}
    media = MediaFileUpload(filename,
                            mimetype='video/mp4')
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()
    # print('File ID: %s' % file.get('id'))
    print(f"Uploaded {filename} to Google Drive")

def record():
    # Record a 10-second video
    current_time = datetime.now()
    time_str = current_time.strftime('%Y-%m-%d_%H-%M-%S')
    unique_filename = f"dance_recording_{time_str}.mp4"
    print(f"Recording to {unique_filename}")

    record_video(output_file=unique_filename, record_time=3)

    # wait until unique_filename.mp4 is created, then upload it to Google Drive
    while True:
        if os.path.exists(unique_filename):
            print("it exists!")
            upload_video(unique_filename)
            break

if __name__ == "__main__":
    record()