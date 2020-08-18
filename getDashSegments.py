import json, os, wget, urllib, ssl, re, argparse, shutil
from pathlib import Path
from subprocess import Popen, PIPE

class segmentGenerator:
    def __init__(self, mpdSummary, playbackReference):
        self.mpdSummary = mpdSummary
        self.playbackReference = playbackReference
    
    def getSegmentsList(self, repId):
        segmentList = []
        try:
            repInfo = mpdSummary['videoRepresentations'][repId]
        except KeyError:
            print (f'no key found with id "{repId}"')
            return
        baseUrl =  self.mpdSummary['baseUrl']+self.mpdSummary['periodUrl']
        for mediaFile in playbackReference:
            time = mediaFile['startTime']*mediaFile['timescale']
            number = mediaFile['index']+1
            segmentName = getSegmentName(repInfo['media'], time,number,repId)
            segmentName = baseUrl + segmentName
            segmentList.append(segmentName)
        return segmentList

    def getInitFile(self, repId):
        try:
            repInfo = mpdSummary['videoRepresentations'][repId]
        except KeyError:
            print (f'no key found with id "{repId}"')
            return
        baseUrl =  self.mpdSummary['baseUrl']+self.mpdSummary['periodUrl']
        segmentName = getSegmentName(repInfo['initialization'], None,None,repId)
        segmentName = baseUrl + segmentName
        return segmentName


def getSegmentName (SegmentTemplate, time, number, repID):
    print (SegmentTemplate)
    segment = SegmentTemplate
    segment = segment.replace('$RepresentationID$', repID)
    if (time != None and number != None):
        segment = segment.replace('$Time$', '%d' % time)
        print (segment)
        fmt = getNumberAtr (segment)
        if fmt == "": fmt = '%d'
        segment = segment.replace('$Number' + fmt + '$', fmt % number)
    print (segment)
    return segment

def getNumberAtr(SegmentTemplate):
    try:
        atributes = re.search(r'\$Number(.+?)\$', SegmentTemplate).group(1)
    except AttributeError:
        atributes = ''
    return atributes


def getNamefromMpd (mpdUrl):
        return mpdUrl[mpdUrl.rfind("/")+1:].replace(".mpd","")

def getFileNameFromUrl(url):
    return url[url.rfind("/")+1:]

def checkFolder(folderName):
    path = (os.path.dirname(os.path.abspath(__file__)))
    folderPath = os.path.join (path, folderName )
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    return folderPath
    
def downloadMediaFiles(mediaFilesList, tempFolder):
    for url in mediaFilesList:
        try:
            filePath =  os.path.join (tempFolder, getFileNameFromUrl(url))
            if mediaFileExists(filePath): os.remove(filePath)
            wget.download(url, out=tempFolder)
        except urllib.error.HTTPError as e: 
            print(e, url)
            continue

def downloadInitFile (iniFileUrl, tempFolder):
    filePath =  os.path.join (tempFolder, getFileNameFromUrl(iniFileUrl))
    if mediaFileExists(filePath): os.remove(filePath)
    try:
        wget.download(mediaFilesByRepresentation[repId]['initSeg'], out=tempFolder)
    except urllib.error.HTTPError as e: 
        print(e, iniFileUrl)

def mediaFileExists(filePath):
    if Path(filePath).is_file(): return True
    else: return False

def cleanFile(f):
    return f.split("?")[0] 

def get_args():
    '''This function parses and return arguments passed in'''
    parser = argparse.ArgumentParser(prog = 'dashjsDownloader', description = 'script to download Dash mediaFiles based on a Playback log history. The downloaded media files (one per Dash representation) are saved locally')
    parser.add_argument('jsonFile' , type = str, help = 'File with information about the playback mediasegments to download. The file must be generated using github.com/gdavila/vmaf-framework instructions ')
    parser.add_argument('--extraFile' , help =  'Load extraRepresentations.json to add manually extra representations that are not on the jsonFile. (Default: dissable)', action = 'store_true')
    return parser.parse_args()



if __name__ == '__main__':

    ssl._create_default_https_context = ssl._create_unverified_context
    cmdParser=get_args()
    srcFile =  cmdParser.jsonFile # playback Src info
    extraFileFlag = cmdParser.extraFile

    #open json src file
    with open(srcFile, 'r') as f:
        mediaFilesInfo = json.load(f)


    #Getting info
    if extraFileFlag:
        extraFile="extraRepresentations.json"
        try:
            with open(extraFile, 'r') as f: representations = json.load(f)
        except:
            representations = {}
            print("No extra File founded")

    else: representations = {}
    
    try: 
        extraInfo = representations['Representations']
        print("Extra representations loaded")  
    except KeyError: 
        extraInfo = []
        print("No extra representations")


    #check if folder exists, if not it is created
    tempFolder = checkFolder('TempMedia')
    mediaFolder = checkFolder('Media')
    serviceName = getNamefromMpd(mediaFilesInfo['mpdSummary']['mpdUrl']).replace(" ", "")
    mpdSummary = mediaFilesInfo['mpdSummary']
    playbackReference = mediaFilesInfo['MediaFiles']
    segments = segmentGenerator(mpdSummary, playbackReference)
    mediaFilesByRepresentation = {}
    for repId in mpdSummary['videoRepresentations']:
        mediaFilesByRepresentation[repId] = {}
        mediaFilesByRepresentation[repId]['mediaSeg'] = segments.getSegmentsList(repId)
        mediaFilesByRepresentation[repId]['initSeg'] = segments.getInitFile(repId)

    mimeType= mediaFilesInfo['MediaInfo']['mimeType']

    #Downloading and Concat
    serviceFolder = checkFolder('Media/'+ serviceName)
    for repId in mediaFilesByRepresentation:
        #Downloading 
        print("Downloading %s ..." % repId)
        downloadInitFile(mediaFilesByRepresentation[repId]['initSeg'], tempFolder )
        downloadMediaFiles(mediaFilesByRepresentation[repId]['mediaSeg'], tempFolder )
        initFile = getFileNameFromUrl(mediaFilesByRepresentation[repId]['initSeg'])
        initFile = cleanFile(initFile)
        mediaFiles=[]
        for i in mediaFilesByRepresentation[repId]['mediaSeg']:
            tempMediaFile = getFileNameFromUrl(i)
            tempMediaFile = cleanFile(tempMediaFile)
            if Path(os.path.join(tempFolder, tempMediaFile)).is_file():
                mediaFiles.append(tempMediaFile)
            else: pass
        print("Creating  %s media file..." % repId)
        print(mediaFiles)
        catCmd = ['cat'] + [initFile] + mediaFiles + ['>'] + ["\""+serviceFolder +"/"+repId + "." + mimeType[mimeType.rfind("/")+1:] + "\""]
        os.chdir(tempFolder)
        process = Popen(' '.join(catCmd), shell=True, stdout=PIPE)
        print (' '.join(catCmd))
        process.wait()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
    print ("Cleaning")
    shutil.rmtree(tempFolder)
