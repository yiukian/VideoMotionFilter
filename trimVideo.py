import sys, getopt
import constant
from datetime import datetime
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


ARG_OPT = "hi:o:s:e:"


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

def showHelp(progName):
    print(progName + " Usage:\n")
    print("\n\tTrim video without encode/decode")
    print("\n\tOptions:")
    print("\n\t\th: Show help")
    print("\n\t\ti: Input video file")
    print("\n\t\to: Output video file")
    print("\n\t\ts: Start time in format hh:mm:ss:ff")
    print("\n\t\te: Stop  time in format hh:mm:ss:ff")
    print("\n\n")

def main(argv):

    print("Incomplete code")
    sys.exit(0)

    # Parse input arguments
    try:
        opts, args = getopt.getopt(argv[1:], ARG_OPT, "")
    except getopt.GetoptError:
        showHelp(argv[0])
        sys.exit(0)

    

if __name__ == "__main__":
    main(sys.argv)


