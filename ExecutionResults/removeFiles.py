import os
import sys
from pathlib import Path

OPER_FLAG_FORCE     = 'f'

def removeFiles(fileListPath, flag):
    count = 0
    if os.path.isfile(fileListPath):
        with open(fileListPath) as filesList:
            for filePath in filesList:
                # on situation: f.rstrip('\n')
                # or, if you get rid of os.chdir(path) above,
                # fname = os.path.join(path, f.rstrip())
                filePath = filePath.rstrip()
                if os.path.isfile(filePath):  # this makes the code more robust
                    count += 1
                    fileSize = os.stat(filePath).st_size/1024.0
                    if flag == OPER_FLAG_FORCE:
                        os.remove(filePath)
                        print('{:04d}    Removed {}   {:,.2f} MB'.format(count, filePath, fileSize))
                    else:
                        print("{:04d}    {}  to be removed    {:,.2f} MB".format(count, filePath, fileSize))

                elif filePath != "":
                    print("Invalid file ", filePath)

            print("Total removed files: ", count)


if __name__ == "__main__":

    flag = ''
    filePath = ''

    if len(sys.argv) == 3:
        if(sys.argv[2] == '-f'):    # Force flag
            flag = OPER_FLAG_FORCE
            filePath = sys.argv[1]

    elif len(sys.argv) == 2:
        filePath = sys.argv[1]

    if filePath == '':
        print(
            "Usage:\n\tpython {} [file]\n\n   [file] contains a list of files to be removed.\n\n".format(
                sys.argv[0]
            )
        )
    else:
        if os.path.isfile(filePath):
            removeFiles(filePath, flag)
            print("completed.")
        else:
            print("Invalid file: ", filePath)

