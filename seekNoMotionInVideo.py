import os
import cv2 as cv
import time
import constant

from datetime import datetime
from moviepy.editor import VideoFileClip


totalClips = 0
totalSubClips = 0
totalNoises = 0
clipActualFps = 0

def subclip_filePathToTimestamp(filePath, rootPath):
    # rootPath\YYYYMMDD\hh\hhmmss
    filePath = filePath.replace(rootPath, "").split('\\')
    # make it become YYYYMMDDhhmmss
    filePath = filePath[1] + filePath[3]
    #print(filePath)
    clipDateTime = datetime.strptime(filePath, "%Y%m%d%H%M%S.mp4")
    return datetime.timestamp(clipDateTime)


def subclip_saveClipInfo(fileHandle, rawFileName, timestamp, clipStartFrame, clipStopFrame):
    global clipActualFps
    clipStartSec = clipStartFrame / clipActualFps
    clipStopSec  = clipStopFrame / clipActualFps
    outFileSuffix = datetime.fromtimestamp(timestamp + clipStartSec).strftime("%Y%m%d-%H%M%S")
    print('\rMotion  {:4.3f}s - {:4.3f}s   [{:.3f}s]  [{}.mp4]'.format(clipStartSec, clipStopSec, (clipStopSec-clipStartSec), outFileSuffix))
    print('Motion,{},{}.mp4,{:.3f},{:.3f},{:.3f}s'.format(rawFileName, outFileSuffix, (timestamp+clipStartSec), (timestamp+clipStopSec), (clipStopSec-clipStartSec)), file=fileHandle)


def subclip_saveNoiseInfo(fileHandle, rawFileName, timestamp, clipStartFrame, clipStopFrame):
    clipStartSec = clipStartFrame / clipActualFps
    clipStopSec  = clipStopFrame / clipActualFps
    outFileSuffix = datetime.fromtimestamp(timestamp + clipStartSec).strftime("%Y%m%d-%H%M%S")
    print('\rNoise   {:4.3f}s - {:4.3f}s   [{:.3f}s]  [{}.mp4]'.format(clipStartSec, clipStopSec, (clipStopSec-clipStartSec), outFileSuffix))
    print('Noise,{},{}.mp4,{:.3f},{:.3f},{:.3f}s'.format(rawFileName, outFileSuffix, (timestamp+clipStartSec), (timestamp+clipStopSec), (clipStopSec-clipStartSec)), file=fileHandle)


def subclip_logDamaged(filePath, outFilePathPrefix):
    fileLog = open(outFilePathPrefix + '\\' + constant.FILE_DAMAGED_VIDEO, 'a')
    print(filePath, file=fileLog)
    fileLog.close()


def subclip_seekNoMotionInVideo(inFilePath, inFilePathPrefix, outFilePathPrefix):

    global clipActualFps
    global totalClips
    global totalSubClips
    global totalNoises

    print('\n{:03d} - {}'.format(totalClips, inFilePath))

    timeStt = datetime.timestamp(datetime.now())
    #print("Analysis ", inFilePath)

    try:
        cap = None
        cap = VideoFileClip(inFilePath)
        if cap.reader == None:
            print('VideoFileClip.reader is None')
            cap.close()
            cap = None
            raise NameError('Failed to read the video file')

        clipDuration   = cap.duration
        cap.close()

        cap = cv.VideoCapture(inFilePath)
        if not cap.isOpened():
            raise NameError('Failed to open the video file')

    except cv.error as e:
        print('CV Error---:::: Damaged file: ', inFilePath)
        subclip_logDamaged(inFilePath, outFilePathPrefix)
        if cap != None: cap.release()
        return False        # Return False for damaged file

    except Exception as e:
        print('Exception---:::: Damaged file: ', inFilePath)
        subclip_logDamaged(inFilePath, outFilePathPrefix)
        if cap != None: cap.release()
        return False        # Return False for damaged file

    else:
        clipTimestamp  = subclip_filePathToTimestamp(inFilePath, inFilePathPrefix)
        clipWidth      = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        clipHeight     = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        clipBitrate    = int(cap.get(cv.CAP_PROP_BITRATE))
        clipFormat     = int(cap.get(cv.CAP_PROP_FORMAT))
        clipFrameCount = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
        clipMode       = int(cap.get(cv.CAP_PROP_MODE))
        clipFps        = cap.get(cv.CAP_PROP_FPS)
        if clipDuration > 0:
            clipActualFps  = clipFrameCount/clipDuration
        else:
            clipActualFps = constant.CLIP_FPS_FOR_RTC

        print('dimension        : {} x {} '.format(clipWidth, clipHeight))
        print('fps              :', clipFps)
        print('Actual fps       :', clipActualFps)
        print('bitrate          :', clipBitrate)
        print('frame count      :', clipFrameCount)
        print('Duration(s)      :', clipDuration)
        print('format           :', clipFormat)
        print('mode             :', clipMode)

        fileRec = open(outFilePathPrefix + r'\videoList.csv', 'a')

        cv.namedWindow('Found Motion', cv.WINDOW_NORMAL)
        cv.resizeWindow('Found Motion', constant.PREVIEW_W_SIZE, int(clipHeight*constant.PREVIEW_W_SIZE/clipWidth))

        ret, frame1 = cap.read()
        if ret: ret, frame1 = cap.read()    # skip this frame
        if ret: ret, frame2 = cap.read()    # skip this frame
        if ret: ret, frame2 = cap.read()

        frameId = 4
        nextRefresh = constant.UI_REFRESH_DURA_FRAMES
        subclip_stt = -1
        subclip_stp = -1

        totalSubClips = 0
        totalNoises = 0

        while (ret and cap.isOpened()):

            diff = cv.absdiff(frame1, frame2)
            diff_gray = cv.cvtColor(diff, cv.COLOR_BGR2GRAY)
            blur = cv.GaussianBlur(diff_gray, (5, 5), 0)
            _, thresh = cv.threshold(blur, 20, 255, cv.THRESH_BINARY)
            dilated = cv.dilate(thresh, None, iterations=3)
            contours, ret = cv.findContours(dilated, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            # ret = None or [[[-1 -1 -1 -1]]]  if no contour found

            if len(contours) > 1:

                # Check valid motion
                countMotion = 0
                for contour in contours:
                    if cv.contourArea(contour) > 1600:
                        countMotion += 1
                        (x, y, w, h) = cv.boundingRect(contour)
                        cv.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)

                if countMotion > 0:
                    # Found motion
                    if subclip_stt == -1:
                        # Start of motion, set subclip_stt
                        subclip_stt = frameId

                    # Trace motion continunity and update the subclip_stp
                    subclip_stp = frameId

                    print('\r     [{} - {}, {}] [{}] [{}]'.format(subclip_stt, subclip_stp, frameId, (subclip_stp-subclip_stt), (frameId-subclip_stp)))
                    cv.imshow("Found Motion", frame1)
                    if cv.waitKey(1) == 27:
                        break

            else:
                # No motion found
                if subclip_stt != -1 and (frameId - subclip_stp) > constant.NOISE_WINDOW_FRAME:
                    # Previous motion stopped after NOISE_WINDOW_FRAME
                    if (subclip_stp - subclip_stt) > constant.MIN_MOTION_DURA_FRAMES:
                        # Save clip info if the clip duration is longer than MIN_MOTION_DURA_FRAMES
                        totalSubClips += 1
                        subclip_saveClipInfo(fileRec, inFilePath, clipTimestamp, subclip_stt, subclip_stp)
                    else:
                        # Save noise position
                        totalNoises += 1
                        subclip_saveNoiseInfo(fileRec, inFilePath, clipTimestamp, subclip_stt, subclip_stp)

                    # Reset subclip tags
                    subclip_stt = -1
                    subclip_stp = -1

            frame1 = frame2
            ret, frame2 = cap.read()            # skip this frame
            if ret: ret, frame2 = cap.read()    # skip this frame
            if ret: ret, frame2 = cap.read()    # skip this frame
            if ret: ret, frame2 = cap.read()
            frameId = int(cap.get(cv.CAP_PROP_POS_FRAMES))

            if frameId >= nextRefresh:
                nextRefresh += constant.UI_REFRESH_DURA_FRAMES
                print('\r{}'.format(frameId), end='')
                if cv.waitKey(1) == 27:
                    break

        if subclip_stt != -1:
            # Save last subclip
            if (subclip_stp - subclip_stt) > constant.MIN_MOTION_DURA_FRAMES:
                # Save clip info if the clip duration is longer than MIN_MOTION_DURA_FRAMES
                totalSubClips += 1
                subclip_saveClipInfo(fileRec, inFilePath, clipTimestamp, subclip_stt, subclip_stp)
            else:
                # Save noise position
                totalNoises += 1
                subclip_saveNoiseInfo(fileRec, inFilePath, clipTimestamp, subclip_stt, subclip_stp)


        timeUsed = datetime.timestamp(datetime.now()) - timeStt
        print('\r{}  - Time used: {:.1f}'.format(frameId, timeUsed))
        print('Motion Found: {},  Noise Found: {}'.format(totalSubClips, totalNoises))

        cap.release()
        fileRec.close()
        cv.destroyAllWindows()
        
        if totalSubClips > 0:
            return False        # Found useful subclip
        
        return True             # No Motion found


if __name__ == "__main__":

    inFolder = constant.FILEIN_ROOTPATH
    outFolder = constant.FILEOUT_ROOTPATH

    #inFile = r'c:\temp\in\20161030\16\162225.mp4'
    #inFile = r'c:\temp\in\20161030\15\132149.mp4'
    inFile = r'c:\temp\in\20161030\13\135220.mp4'
    subclip_seekNoMotionInVideo(inFile, inFolder, outFolder)



