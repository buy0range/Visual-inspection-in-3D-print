# Visual-inspection-in-3D-print
## Overview
This project is a video processing tool that integrates real-time video analysis and image processing capabilities. The program detects changes in video frames and performs Canny edge detection. It also includes an alert system to send emails when anomalies are detected.

---

## 项目概述
本项目是一个集实时视频分析与图像处理功能于一体的视频处理工具。程序能够检测视频帧的变化，并进行 Canny 边缘检测。项目还包括一个异常警报系统，当检测到问题时发送邮件提醒。

## Features 功能特性
- **Real-time Video Processing 实时视频处理**: Analyze frames from a live camera feed 分析摄像头实时画面。
- **File-based Video Processing 文件视频处理**: Extract and process frames from video files 从视频文件中提取并处理帧。
- **Region of Interest (ROI) Selection 感兴趣区域选择**: Select a specific region for processing 选择特定区域进行处理。
- **Canny Edge Detection Canny 边缘检测**: Apply edge detection to processed frames 对处理后的帧进行边缘检测。
- **Anomaly Detection 异常检测**: Identify problematic frames and send alerts via email 识别问题帧并通过邮件发送警报。
- **Graphical User Interface (GUI) 图形用户界面**: User-friendly interface for easy interaction 用户友好的界面，方便操作。

## Requirements 环境要求
- Python 3.7 or higher / Python 3.7 或更高版本
- Required Libraries 所需依赖库:
  ```bash
  numpy
  opencv-python
  skimage
  yagmail
  tkinter
  ```

## Installation 安装步骤
1. Clone the repository 克隆项目:
   ```bash
   git clone <repository_url>
   ```
2. Install dependencies 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

## Usage 使用方法
1. Run the program 运行程序:
   ```bash
   python 终极无敌宇宙暴龙战神.py
   ```
2. Select processing mode (real-time or file-based) 选择处理模式（实时或文件视频处理）。
3. Set folders and parameters through the GUI 在 GUI 中设置文件夹和参数。
4. Monitor progress via the GUI 通过 GUI 监控处理进度。

## Notes 注意事项
- Ensure the camera is connected for real-time processing 运行实时处理前，请确保摄像头已连接。
- Configure the sender email (`sender_email`) and authorization code in the `auto_mail` function 在 `auto_mail` 函数中配置发件邮箱 (`sender_email`) 和授权码。

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
