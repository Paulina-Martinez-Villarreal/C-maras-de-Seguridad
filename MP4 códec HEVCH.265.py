import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess

class VideoApp:
    def __init__(self, root, url):
        self.root = root
        self.root.title("RTSP Stream Viewer")

        self.url = url
        self.cap = cv2.VideoCapture(self.url)
        
        if not self.cap.isOpened():
            print("Error: Could not open stream.")
            exit()
        
        # Create a label in the GUI to display the video frames
        self.video_label = tk.Label(root)
        self.video_label.pack()

        # Create buttons
        self.start_button = ttk.Button(root, text="Start", command=self.start_stream)
        self.start_button.pack(side=tk.LEFT)
        
        self.stop_button = ttk.Button(root, text="Stop", command=self.stop_stream)
        self.stop_button.pack(side=tk.LEFT)

        self.record_button = ttk.Button(root, text="Record", command=self.toggle_recording)
        self.record_button.pack(side=tk.LEFT)

        self.quit_button = ttk.Button(root, text="Quit", command=root.quit)
        self.quit_button.pack(side=tk.LEFT)

        # Flags to control the streaming and recording
        self.streaming = False
        self.recording = False

        # Video writer for recording
        self.ffmpeg_process = None

    def start_stream(self):
        self.streaming = True
        self.show_frame()

    def stop_stream(self):
        self.streaming = False
        self.recording = False  # Stop recording if the stream is stopped
        if self.ffmpeg_process:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.wait()
            self.ffmpeg_process = None

    def toggle_recording(self):
        if self.recording:
            self.recording = False
            self.record_button.config(text="Record")
            if self.ffmpeg_process:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.wait()
                self.ffmpeg_process = None
        else:
            self.recording = True
            self.record_button.config(text="Stop Recording")
            self.start_ffmpeg_process()

    def start_ffmpeg_process(self):
        ffmpeg_command = [
            'ffmpeg',
            '-y',  # Overwrite output files without asking
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', '1920x1080',  # Frame size
            '-r', '20',  # Frame rate
            '-i', '-',  # Input from stdin
            '-c:v', 'libx265',  # HEVC codec
            '-pix_fmt', 'yuv420p',
            'outpu.mp4'
        ]
        self.ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

    def show_frame(self):
        if self.streaming:
            ret, frame = self.cap.read()
            if ret:
                # Resize the frame to 480p
                desired_width = 1920
                desired_height = 600
                frame = cv2.resize(frame, (desired_width, desired_height))

                # Convert the frame to ImageTk format
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

                # If recording, write the frame to the FFmpeg process
                if self.recording and self.ffmpeg_process:
                    self.ffmpeg_process.stdin.write(frame.tobytes())
            else:
                print("Error: Failed to capture frame.")

            # Call this method again after a delay
            self.root.after(10, self.show_frame)

    def on_closing(self):
        self.streaming = False
        if self.ffmpeg_process:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.wait()
        self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoApp(root, "rtsp://admin:123456aA@192.168.137.73/live/ch00_0")
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
