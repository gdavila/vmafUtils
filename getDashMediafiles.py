import json, os, wget, urllib, ssl, re, argparse, shutil
from pathlib import Path
from subprocess import Popen, PIPE

def createUrl(referenceUrl, representationId_old, representationId_new, serviceLocation):
    newUrl = removeServiceLocation(referenceUrl, serviceLocation)
    if representationId_old.isdigit():
        newUrl = re.sub(r'(?<=\W)[' + representationId_old + ']+(?=\W)', representationId_new, '/'+newUrl)[1:]
        return serviceLocation + newUrl
    else: 
        newUrl = newUrl.replace(representationId_old, representationId_new)
        return serviceLocation + newUrl

def removeServiceLocation(referenceUrl, serviceLocation):
    return referenceUrl[re.match(serviceLocation,referenceUrl).end():]

def generateMediaFiles (representationList, playbackReference):
    mediaFilesByRepresentation = {}
    for repId in representationList:
        mediaFilesByRepresentation[repId] = {}
        mediaFilesByRepresentation[repId]['mediaSeg'] = []
        for mediaFile in playbackReference:
            referenceUrl = mediaFile['url']
            repId_old = mediaFile['representationId']
            serviceLocation = mediaFile['serviceLocation']
            newUrl = createUrl(referenceUrl, repId_old, repId, serviceLocation )
            if mediaFile['type'] == 'InitializationSegment': 
                mediaFilesByRepresentation[repId]['iniSeg'] = newUrl
            elif mediaFile['type'] == 'MediaSegment':
                mediaFilesByRepresentation[repId]['mediaSeg'].append(newUrl)
    return mediaFilesByRepresentation

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

def downloadIniFile (iniFileUrl, tempFolder):
    filePath =  os.path.join (tempFolder, getFileNameFromUrl(iniFileUrl))
    if mediaFileExists(filePath): os.remove(filePath)
    try:
        wget.download(mediaFilesByRepresentation[repId]['iniSeg'], out=tempFolder)
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

    serviceName = getNamefromMpd(mediaFilesInfo['MpdUrl']).replace(" ", "") # List of desired representations
    representationList = mediaFilesInfo['Representations'] + extraInfo# List of desired representations
    playbackReference = mediaFilesInfo['MediaFiles'] # List of reference url during playback
    mediaFilesByRepresentation = generateMediaFiles(representationList, playbackReference)
    mimeType= mediaFilesInfo['MediaInfo']['mimeType']

    #Downloading and Concat
    serviceFolder = checkFolder('Media/'+ serviceName)
    for repId in mediaFilesByRepresentation:
        #Downloading 
        print("Downloading %s ..." % repId)
        downloadIniFile(mediaFilesByRepresentation[repId]['iniSeg'], tempFolder )
        downloadMediaFiles(mediaFilesByRepresentation[repId]['mediaSeg'], tempFolder )
        initFile = getFileNameFromUrl(mediaFilesByRepresentation[repId]['iniSeg'])
        initFile = cleanFile(initFile)
        mediaFiles=[]
        for i in mediaFilesByRepresentation[repId]['mediaSeg']:
            temMediaFile = getFileNameFromUrl(i)
            temMediaFile = cleanFile(temMediaFile)
            if Path(os.path.join(tempFolder, temMediaFile)).is_file():
                mediaFiles.append(temMediaFile)
            else: pass
        print("Creating  %s media file..." % repId)
        print(mediaFiles)
        catCmd = ['cat'] + [initFile] + mediaFiles + ['>'] + ["\""+serviceFolder +"/"+repId + "." + mimeType[mimeType.rfind("/")+1:] + "\""]
        os.chdir(tempFolder)
        process = Popen(' '.join(catCmd), shell=True, stdout=PIPE)
        #process.communicate()
        print (' '.join(catCmd))
        process.wait()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
    print ("Cleaning")
    shutil.rmtree(tempFolder)
