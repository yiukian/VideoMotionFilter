import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt



def motionDetection():
    cap = cv.VideoCapture("./103009.mp4")
    # cap = cv.VideoCapture("./vtest.avi")
    ret, frame1 = cap.read()
    """
     if ret: ret, frame1 = cap.read()    # skip this frame
    if ret: ret, frame1 = cap.read()
    if ret: ret, frame2 = cap.read()    # skip this frame
    if ret: ret, frame2 = cap.read()    # skip this frame
    if ret: ret, frame2 = cap.read()    # skip this frame
    """
    if ret:
        ret, frame2 = cap.read()

    while cap.isOpened():
        diff = cv.absdiff(frame1, frame2)
        diff_gray = cv.cvtColor(diff, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(diff_gray, (5, 5), 0)
        _, thresh = cv.threshold(blur, 20, 255, cv.THRESH_BINARY)
        dilated = cv.dilate(thresh, None, iterations=3)
        contours, ret = cv.findContours(dilated, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        # ret = None or [[[-1 -1 -1 -1]]]  if no contour found
        # print(ret)

        for contour in contours:
            (x, y, w, h) = cv.boundingRect(contour)
            if cv.contourArea(contour) < 1600:
                continue
            cv.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # cv.putText(frame1, "Status: {}".format('Movement'), (10, 20), cv.FONT_HERSHEY_SIMPLEX,
            #           1, (255, 0, 0), 3)

        # cv.drawContours(frame1, contours, -1, (0, 255, 0), 2)

        cv.imshow("Video", frame1)
        frame1 = frame2
        ret, frame2 = cap.read()  # skip this frame
        if ret:
            ret, frame2 = cap.read()  # skip this frame
        if ret:
            ret, frame2 = cap.read()  # skip this frame
        if ret:
            ret, frame2 = cap.read()

        if cv.waitKey(1000) == 27:
            break

    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    motionDetection()


"""     
######## Some useful code #############
#
## Extract a portion of a movie without decoding/encoding
#
#from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
#ffmpeg_extract_subclip("video1.mp4", start_time, end_time, targetname="test.mp4")
#
#
## Installation of moviepy
#pip install --trusted-host pypi.python.org moviepy
#pip install imageio-ffmpeg
#

from moviepy.editor import VideoFileClip, concatenate_videoclips

clip1 = VideoFileClip("1.mp4")
clip2 = VideoFileClip("2.mp4")
clip3 = VideoFileClip("3.mp4")

finalclip = concatenate_videoclips([clip1, clip2, clip3])
finalclip.write_videofile("out.mp4") # 寫出檔案out.mp4


import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.audio.io.AudioFileClip import AudioFileClip

def videoConcat(name, videos, path="./"):
    # 函數功能: 將videos內的視頻首尾相接，輸出name
    # ex: videoConcat("out.mp4", ["1.mp4", "2.mp4", "3.mp4"],"./music")
    # NOTE: 每個影片的畫面長寬需一致
    origin_path = os.getcwd()
    os.chdir(path)
    finalclip = concatenate_videoclips([VideoFileClip(v) for v in videos])
    finalclip.write_videofile(name)
    os.chdir(origin_path)

# 函數功能: 在指定路徑下，從in_video截取t1~t2秒的視頻，輸出out_video
# ex: mySubclip("1.mp4", "out.mp4", 10, 15,'./music')，參數可接受浮點數
#
def mySubclip(in_video, out_video, t1, t2, path="./"):

    origin_path = os.getcwd()
    os.chdir(path)
    with VideoFileClip(in_video) as video:
        video_clip = video.subclip(t1, t2)
        video_clip.write_videofile(out_video)
    os.chdir(origin_path)


def myAudioclip(in_video, out_audio, path="./"):
    # 函數功能: 在指定路徑下，截取in_video的聲音檔，輸出out_audio
    # ex: mySubclip("1.mp4", "out.mp3", './music')
    origin_path = os.getcwd()
    os.chdir(path)
    audio_clip = AudioFileClip(in_video)
    audio_clip.write_audiofile(out_audio)
    os.chdir(origin_path)

 """
