import json
import argparse
import re
import os

def get_args():
    parser = argparse.ArgumentParser(prog = 'mediainfo2csv')
    parser.add_argument('input' , type = str, help = 'input file')
    return parser.parse_args()

def getValue(string):
    s = string.split(":",1)[1]
    s = re.sub(r"\s+", '', s)
    return s

def getIntValue(string):
    n = string.split(":",1)[1]
    n = re.sub("[^0-9]", "", n)
    return n
    
if __name__ == '__main__':
    cmdParser=get_args()
    mediaInfoFile = cmdParser.input
    fileName=None
    profile = None
    bitrate = None
    width = None
    height = None
    csventry = None
    header = ["fileName", "resolution", "bitrate", "profile"]
    csvData = []
    data=[]
    csv_file = os.path.splitext(mediaInfoFile)[0]+ '.csv'

    with open (mediaInfoFile,"r") as f:
        for line in f.readlines():
            if "Complete name" in line:
                csventry = {}
                csventry['fileName']= getValue (line)
            if "Format profile" in line:
                csventry['profile'] = getValue (line)

            if "Bit rate" in line:
                csventry['bitrate'] = getIntValue (line)

            if "Width" in line:
                csventry['width'] =  getIntValue (line)

            if "Height" in line:
                csventry['height'] = getIntValue (line)


            if len(csventry.keys()) ==5:
                data = [csventry['fileName'], f'{csventry["width"]}x{csventry["height"]}', csventry['bitrate'], csventry['profile']]
                csvData.append(data)

    
    with open(csv_file, 'w') as csvFile:
        csvFile.write(";".join(header))
        csvFile.write('\n')
        for line in csvData:
            csvFile.write(";".join(str(i) for i in line))
            csvFile.write('\n')