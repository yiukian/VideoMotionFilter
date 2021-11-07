import os
import cv2 as cv
import constant

from win32_setfiletime import setctime, setmtime, setatime
from datetime import datetime
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip


#from matplotlib import pyplot as plt
totalClips = 0
totalSubClips = 0
totalNoises = 0
clipActualFps = 0

def subclip_filePathToTimestamp(filePath, rootPath):
    # rootPath\YYYYMMDD\hh\hhmmss
    filePath = filePath.replace(rootPath, "").split('\\')
    # make it become YYYYMMDDhhmmss
    filePath = filePath[1] + filePath[3]
    print(filePath)
    clipDateTime = datetime.strptime(filePath, "%Y%m%d%H%M%S.mp4")
    return datetime.timestamp(clipDateTime)


def subclip_setFileTime(filePath, createTimestamp, modifiedTimestamp):
    #winfile = win32file.CreateFile(filePath, win32con.GENERIC_WRITE,
    #win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
    #None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None)

    #win32file.SetFileTime(winfile, createTimestamp, modifiedTimestamp, modifiedTimestamp)
    setctime(filePath, createTimestamp)
    setmtime(filePath, modifiedTimestamp)
    setatime(filePath, modifiedTimestamp)


def subclip_saveClipInfo(fileHandle, rawFileName, timestamp, clipStartFrame, clipStopFrame):
    global clipActualFps
    clipStartSec = clipStartFrame / clipActualFps
    clipStopSec  = clipStopFrame / clipActualFps
    outFileSuffix = datetime.fromtimestamp(timestamp + clipStartSec).strftime("%Y%m%d-%H%M%S")

    print('\rMotion  {:04.3f}s - {:04.3f}s   [{:.3f}s]  [{}.mp4]'.format(clipStartSec, clipStopSec, 
        (clipStopSec-clipStartSec), outFileSuffix))

    print('Motion,{},{}.mp4,{:.3f},{:.3f},{:.3f}s,{},{}'.format(rawFileName, outFileSuffix, 
        (timestamp+clipStartSec), (timestamp+clipStopSec), (clipStopSec-clipStartSec), 
        clipStartFrame, clipStopFrame), file=fileHandle)


def subclip_saveNoiseInfo(fileHandle, rawFileName, timestamp, clipStartFrame, clipStopFrame):
    clipStartSec = clipStartFrame / clipActualFps
    clipStopSec  = clipStopFrame / clipActualFps
    outFileSuffix = datetime.fromtimestamp(timestamp + clipStartSec).strftime("%Y%m%d-%H%M%S")

    print('\rNoise   {:04.3f}s - {:04.3f}s   [{:.3f}s]  [{}.mp4]'.format(clipStartSec, clipStopSec, 
        (clipStopSec-clipStartSec), outFileSuffix))

    print('Noise,{},{}.mp4,{:.3f},{:.3f},{:.3f}s,{},{}'.format(rawFileName, outFileSuffix, 
        (timestamp+clipStartSec), (timestamp+clipStopSec), (clipStopSec-clipStartSec), 
        clipStartFrame, clipStopFrame), file=fileHandle)


def subclip_logDamaged(filePath, outFilePathPrefix):
    fileLog = open(outFilePathPrefix + '\\' + constant.FILE_DAMAGED_VIDEO, 'a')
    print(filePath, file=fileLog)
    fileLog.close()


def subclip_logNoMotion(filePath, outFilePathPrefix):
    fileLog = open(outFilePathPrefix + '\\' + constant.FILE_NO_MOTION, 'a')
    print(filePath, file=fileLog)
    fileLog.close()


"""
NOTE: The best way to retrieve the subclip should use frame IDs as the fps is not constant
throughout the clip due to missing frame in streaming when recording
"""
def subclip_retrieve(inFile, outFilePrefix, timestamp, clipStartFrame, clipStopFrame):
    global clipActualFps
    clipStartSec = clipStartFrame / constant.CLIP_FPS_FOR_FFMPEG
    clipStopSec  = clipStopFrame / constant.CLIP_FPS_FOR_FFMPEG
    clipStart_ts = timestamp + (clipStartFrame / clipActualFps)
    clipStop_ts  = timestamp + (clipStopFrame / clipActualFps)
    print('**** [{:.3f} - {:.3f}], [{:.3f} - {:.3f}]'.format(clipStartSec, clipStopSec, clipStart_ts, clipStop_ts))

    outFileSuffix = datetime.fromtimestamp(clipStart_ts).strftime("%Y%m%d-%H%M%S")
    outFile = '{}\\{}.mp4'.format(outFilePrefix, outFileSuffix)

    # TODO: Need another way to extract the subclip since 
    # ffmpeg_extract_subclip extract the subclip by using start/stop time in seconds
    ffmpeg_extract_subclip(inFile, clipStartSec, clipStopSec, targetname=outFile)

    # Keep video clip correct date/time stamp
    subclip_setFileTime(outFile, clipStart_ts, clipStop_ts)


def subclip_extractMotionInVideo(inFilePath, inFilePathPrefix, outFilePathPrefix):

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
        countFrameInMotion = 0

        cv.imshow("Found Motion", frame1)

        while (ret and cap.isOpened()):

            diff = cv.absdiff(frame1, frame2)
            diff_gray = cv.cvtColor(diff, cv.COLOR_BGR2GRAY)
            blur = cv.GaussianBlur(diff_gray, (5, 5), 0)
            _, thresh = cv.threshold(blur, 20, 255, cv.THRESH_BINARY)
            dilated = cv.dilate(thresh, None, iterations=3)
            contours, ret = cv.findContours(dilated, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            # ret = None or [[[-1 -1 -1 -1]]]  if no contour found

            if len(contours) > 1:

                # Check valid contour for motion
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
                    countFrameInMotion += 1

                    cv.imshow("Found Motion", frame1)
                    if cv.waitKey(1) == 27:  break

            else:
                # No motion found
                if subclip_stt != -1:
                    if frameId - subclip_stp > constant.MOTION_WINDOW_FRAME:
                        # No motion in MOTION_WINDOW_FRAME, save the subclip
                        if subclip_stt > constant.CLIP_PREBUF_FRAME:
                            subclip_stt -= constant.CLIP_PREBUF_FRAME
                        else:
                            subclip_stt = 0
                        subclip_stp += constant.CLIP_PROBUF_FRAME
                        totalSubClips += 1
                        subclip_saveClipInfo(fileRec, inFilePath, clipTimestamp, subclip_stt, subclip_stp)
                        subclip_retrieve(inFilePath, constant.FILEOUT_ROOTPATH, clipTimestamp, subclip_stt, subclip_stp)

                        # Reset subclip tags
                        subclip_stt = subclip_stp = -1

                    elif frameId - subclip_stp > constant.NOISE_WINDOW_FRAME:
                        # No motion in NOISE_WINDOW_FRAME, Check noise or not
                        if subclip_stp - subclip_stt <= constant.MIN_MOTION_DURA_FRAMES:
                            # Noise Found
                            totalNoises += 1
                            subclip_saveNoiseInfo(inFilePath, constant.FILEOUT_ROOTPATH, clipTimestamp, subclip_stt, subclip_stp)
                            subclip_stt = subclip_stp = -1

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
            # Motion found
            if subclip_stp - subclip_stt > constant.MIN_MOTION_DURA_FRAMES:
                # Not a noise, save last subclip 
                if subclip_stt > constant.CLIP_PREBUF_FRAME:
                    subclip_stt -= constant.CLIP_PREBUF_FRAME
                else:
                    subclip_stt = 0
                subclip_stp = frameId
                totalSubClips += 1
                subclip_saveClipInfo(fileRec, inFilePath, clipTimestamp, subclip_stt, subclip_stp)
                subclip_retrieve(inFilePath, constant.FILEOUT_ROOTPATH, clipTimestamp, subclip_stt, subclip_stp)
            else:
                totalNoises += 1
                subclip_saveNoiseInfo(inFilePath, constant.FILEOUT_ROOTPATH, clipTimestamp, subclip_stt, subclip_stp)


        timeUsed = datetime.timestamp(datetime.now()) - timeStt
        print('\r{}  - Time used: {:.1f}'.format(frameId, timeUsed))
        print('Motion Found: {},  Noise Found: {}'.format(totalSubClips, totalNoises))

        cap.release()
        fileRec.close()
        cv.destroyAllWindows()

        if totalSubClips > 0:
            return False        # Found useful subclip

        return True             # No Motion found


def extractMotionInVideo_batchProcess(inSubPath, inRootFolder, outRootFolder):
    global totalClips

    with os.scandir(inSubPath) as entries:
        for entry in entries:
            if entry.is_dir():
                if filterSourceFolder(entry.name) == True:
                    extractMotionInVideo_batchProcess(entry.path, inRootFolder, outRootFolder)       # recursively loop all sub-folder

            elif entry.is_file() and entry.name.endswith(".mp4"):
                totalClips += 1
                print('entry.stat().st_size = {}B'.format(entry.stat().st_size))
                if entry.stat().st_size > constant.MIN_VIDEO_FILE_SIZE:
                    ret = subclip_extractMotionInVideo(entry.path, inRootFolder, outRootFolder)
                    if ret:
                        subclip_logNoMotion(entry.path, outRootFolder)
                elif entry.stat().st_size == 0:
                    # File size == 0, no use
                    subclip_logNoMotion(entry.path, outRootFolder)
                else:
                    # File size too small, mark it as damaged
                    print('File size too small---:::: Damaged file: {} [{}B]'.format(entry.path, entry.stat().st_size))
                    subclip_logDamaged(entry.path, outRootFolder)

    entries.close()

def filterSourceFolder(folderName):
    if len(folderName) == 8:
        if int(folderName) < constant.SRC_FOLDER_START:
            print('Skip ', folderName)
            return False

    return True

if __name__ == "__main__":

    inFolder = constant.FILEIN_ROOTPATH
    outFolder = constant.FILEOUT_ROOTPATH
    extractMotionInVideo_batchProcess(inFolder, inFolder, outFolder)

    #inFile = r'c:\temp\in\20161030\16\162225.mp4'
    #subclip_extractMotionInVideo(inFile, inFolder, outFolder)

    #inFile = r'C:\Temp\In\20161030\08\080115.mp4'
    #subclip_extractMotionInVideo(inFile, inFolder, outFolder)

    #inFile = r'C:\Temp\In\20161030\08\081629.mp4'
    #subclip_extractMotionInVideo(inFile, inFolder, outFolder)

    #inFile = r'C:\Temp\In\20161030\08\082637.mp4'
    #subclip_extractMotionInVideo(inFile, inFolder, outFolder)

