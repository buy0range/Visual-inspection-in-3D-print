import os
import cv2
import time
import pathlib
import numpy as np
from tkinter import Entry, Label, Tk, Button, filedialog, messagebox, StringVar, IntVar, ttk
from skimage.metrics import structural_similarity as ssim
import yagmail
# Calculate frame similarity based on SSIM
def is_frame_similar(prev_frame, current_frame, similarity_threshold=0.95):
    mse = ((current_frame - prev_frame) ** 2).mean()
    if mse < 100:  # MSE threshold
        score = ssim(prev_frame, current_frame)
        return score >= similarity_threshold
    return False

def process_realtime_video(output_folder, problem_folder, frame_interval=3, similarity_threshold=0.90):
    pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)
    pathlib.Path(problem_folder).mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    frame_count = 0
    prev_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Cannot capture camera frame")
            break

        frame_count += 1
        if frame_count % frame_interval != 0:
            continue

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(gray_frame, 100, 200)

        if prev_frame is not None and is_frame_similar(prev_frame, gray_frame, similarity_threshold):
            continue

        output_path = pathlib.Path(output_folder) / f"img_{frame_count}.png"
        cv2.imwrite(str(output_path), frame)
        print(f"Frame saved to: {output_path}")

        prev_frame = gray_frame
        cv2.imshow("Canny Edge Detection", canny)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def mp4_2_images(video_path, output_folder, roi, progress_var, similarity_threshold=0.95, frame_interval=5):
    pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)
    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        print("Cannot open video file, please check the path.")
        return

    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_count, num, prev_frame = 0, 0, None

    while True:
        ret, frame = video.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_interval != 0:
            continue

        x, y, w, h = roi
        cropped_frame = frame[y:y + h, x:x + w]
        gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None and is_frame_similar(prev_frame, gray_frame, similarity_threshold):
            continue

        cv2.imwrite(str(pathlib.Path(output_folder) / f'img_{num}.png'), cropped_frame)
        num += 1
        prev_frame = gray_frame

        progress_var.set(int((frame_count / total_frames) * 50))  # Update video extraction progress bar

    video.release()
    print(f"Extracted and saved {num} non-similar frames to '{output_folder}' folder.")

def apply_canny_to_images(input_folder, output_folder, problem_folder, progress_var, top_n=10):
    pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)
    pathlib.Path(problem_folder).mkdir(parents=True, exist_ok=True)

    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))]
    total_images = len(image_files)
    white_pixel_ratios = []
    problem_image_count = 0  # 用于记录问题图片数量
    count_mail = 0 #已经发送的邮件数量

    for i, filename in enumerate(image_files):
        img_path = pathlib.Path(input_folder) / filename
        img = cv2.imread(str(img_path))

        if img is not None:
            canny = cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 50, 200)
            white_ratio = np.sum(canny == 255) / canny.size
            white_pixel_ratios.append((filename, white_ratio))
            cv2.imwrite(str(pathlib.Path(output_folder) / filename), canny)
        else:
            print(f"Cannot load image: {filename}")

        progress_var.set(50 + int((i + 1) / total_images * 50))  # Update Canny processing progress

    # Filter images with the smallest white pixel ratio
    white_pixel_ratios.sort(key=lambda x: x[1])
    filtered_images = white_pixel_ratios[:min(top_n, len(white_pixel_ratios))]

    for filename, _ in filtered_images:
        src_path = pathlib.Path(output_folder) / filename
        dst_path = pathlib.Path(problem_folder) / filename
        cv2.imwrite(str(dst_path), cv2.imread(str(src_path)))

        problem_image_count += 1  # 增加问题图片计数
        
        if problem_image_count >= 5 and count_mail == 0:  # 如果达到5张，发送邮件
            email = receiver_email.get()
            auto_mail(email)  # 使用自动邮件函数
            count_mail += 1
            print("Alert email sent!")
            problem_image_count = 0  # 重置计数

    average_white_ratio = np.mean([white_ratio for _, white_ratio in filtered_images]) if filtered_images else 0
    print(f"Processed images saved to '{problem_folder}' folder, average white pixel ratio: {average_white_ratio:.2%}")


def select_main_folder(output_folder, canny_folder, problem_folder):
    path = filedialog.askdirectory(title="Select main output folder")
    if path:
        try:
            images_output_path = pathlib.Path(path) / "images_output"
            canny_output_path = pathlib.Path(path) / "canny_output"
            problem_output_path = pathlib.Path(path) / "problem_output"

            images_output_path.mkdir(parents=True, exist_ok=True)
            canny_output_path.mkdir(parents=True, exist_ok=True)
            problem_output_path.mkdir(parents=True, exist_ok=True)

            output_folder.set(str(images_output_path))
            canny_folder.set(str(canny_output_path))
            problem_folder.set(str(problem_output_path))

            messagebox.showinfo("Done", f"Main output folder set: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Unable to create folder: {e}")
    else:
        messagebox.showerror("Error", "No main folder selected!")

def auto_mail(receiver_email, retry_interval=5):
    """
    发送警报邮件，失败后会继续重试，直到发送成功。

    参数:
        receiver_email (str): 收件人邮箱地址
        retry_interval (int): 每次重试之间的间隔时间（秒），默认 5 秒。
    """
    # 邮箱配置信息
    sender_email = "fu.tianyi@qq.com"  # 邮箱地址
    password = "wmmrvdeyahjpbgii"      # 邮箱的授权码/应用专用密码

    # 邮件内容
    subject = "!!!Alert!!!"  # 邮件主题
    body = "!!!There is some problem with the machine!!!"
    
    while True:
        try:
            # 初始化 yagmail SMTP 客户端
            yag = yagmail.SMTP(user=sender_email, password=password, host='smtp.qq.com', port=465)
            
            # 发送邮件
            yag.send(
                to=receiver_email,  # 收件人邮箱
                subject=subject,    # 邮件主题
                contents=body       # 邮件内容
            )
            print("Email has been sent successfully")
            # 邮件发送成功后，结束整个程序
            print("Exiting program after email sent.")
            break  # 跳出循环      
        except Exception as e:
            print(f"Fail to send the email: {e}")
            print(f"Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)  # 等待一定时间后重试

def main_gui():
    def start_realtime():
        output_folder = filedialog.askdirectory(title="Select real-time processing output folder")
        if not output_folder:
            messagebox.showwarning("Warning", "No output folder selected!")
            return

        problem_folder = filedialog.askdirectory(title="Select problem image output folder")
        if not problem_folder:
            messagebox.showwarning("Warning", "No problem image folder selected!")
            return

        process_realtime_video(output_folder, problem_folder)

    def select_video_and_folder():
        # Select video file
        video_path_value = filedialog.askopenfilename(title="Select video file", filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if not video_path_value:
            messagebox.showwarning("Warning", "No video file selected!")
            return

        # Select main folder
        main_folder = filedialog.askdirectory(title="Select main folder")
        if not main_folder:
            messagebox.showwarning("Warning", "No main folder selected!")
            return

        # Set selected video path and folder path
        video_path.set(video_path_value)
        output_folder.set(main_folder)
        canny_folder.set(os.path.join(main_folder, "canny_output"))
        problem_folder.set(os.path.join(main_folder, "problem_output"))

        messagebox.showinfo("Done", f"Video file set: {video_path_value} and main folder set: {main_folder}")

    def select_roi():
        cap = cv2.VideoCapture(video_path.get())
        if not cap.isOpened():
            messagebox.showerror("Error", "Cannot open video file!")
            return

        ret, frame = cap.read()
        cap.release()

        if not ret:
            messagebox.showerror("Error", "Cannot read video frame!")
            return

        roi_rect = cv2.selectROI("Select ROI area", frame, fromCenter=False, showCrosshair=True)
        cv2.destroyAllWindows()

        if all(dim > 0 for dim in roi_rect):
            roi.set(str(roi_rect))
            messagebox.showinfo("ROI Selected", f"ROI: {roi_rect}")
        else:
            messagebox.showerror("Error", "Invalid ROI selection!")

    def start_processing():
        if not all([video_path.get(), output_folder.get(), canny_folder.get(), problem_folder.get(), roi.get()]):
            messagebox.showerror("Error", "Please ensure all paths are set!")
            return

        roi_tuple = tuple(map(int, roi.get().strip('()').split(',')))

        try:
            progress_var.set(0)
            mp4_2_images(video_path.get(), output_folder.get(), roi_tuple, progress_var)
            apply_canny_to_images(output_folder.get(), canny_folder.get(), problem_folder.get(), progress_var)
            messagebox.showinfo("Done", "Video processing completed!")
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed: {e}")

    root = Tk()
    root.title("Video Processing Tool")

    video_path = StringVar()
    output_folder = StringVar()
    canny_folder = StringVar()
    problem_folder = StringVar()
    roi = StringVar()
    global receiver_email
    receiver_email = StringVar()


    Label(root, text="Recipient Email:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
    Entry(root, textvariable=receiver_email, width=30).grid(row=0, column=1, padx=10, pady=5)

    # "Real-time video processing" button
    Button(root, text="Real-time Video Processing", command=start_realtime, bg="pink", fg="white").grid(row=1, column=0, columnspan=2, pady=10)

    # "File Video Processing" button
    Button(root, text="File Video Processing", command=select_video_and_folder, bg="blue", fg="white").grid(row=2, column=0, columnspan=2, pady=10)

    Button(root, text="Select ROI Area", command=select_roi, bg="blue", fg="white").grid(row=3, column=0, columnspan=2, pady=10)
    Button(root, text="Start Processing", command=start_processing, bg="green", fg="white").grid(row=4, column=0, columnspan=2, pady=10)

    progress_var = IntVar()
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", variable=progress_var)
    progress_bar.grid(row=5, column=0, columnspan=2, pady=10)

    root.mainloop()

if __name__ == '__main__':
    main_gui()