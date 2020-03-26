import json
import argparse
import os.path
import glob

def get_args():
    parser = argparse.ArgumentParser(prog = 'vmaf2csv')
    parser.add_argument('input' , type = str, help = 'Vmaf input file in json format')
    return parser.parse_args()

if __name__ == '__main__':
    cmdParser=get_args()
    pattern = cmdParser.input
    pattern = os.path.expanduser(pattern)
    
    header = ["frameNum", "VMAF_score", "VMAF_feature_adm2_score", "VMAF_feature_motion2_score", \
                "VMAF_feature_vif_scale0_score", "VMAF_feature_vif_scale1_score", "VMAF_feature_vif_scale2_score", "VMAF_feature_vif_scale3_score", "psnr"  ]
    
    files = glob.glob(pattern)
    for FileName in files:
        csvData = []
        with open (FileName) as jsonFile:
            jsonData = json.load(jsonFile)
            for frame in jsonData['frames']:
                try:
                    csvData.append([frame["frameNum"],\
                                    frame["metrics"]["vmaf"],\
                                    frame["metrics"]["adm2"],\
                                    frame["metrics"]["motion2"],\
                                    frame["metrics"]["vif_scale0"],\
                                    frame["metrics"]["vif_scale1"],\
                                    frame["metrics"]["vif_scale2"],\
                                    frame["metrics"]["vif_scale3"],\
                                    frame["metrics"]["psnr"] \
                                    ])
                except KeyError:
                    csvData.append([frame["frameNum"],\
                                    frame["metrics"]["vmaf"],\
                                    frame["metrics"]["adm2"],\
                                    frame["metrics"]["motion2"],\
                                    frame["metrics"]["vif_scale0"],\
                                    frame["metrics"]["vif_scale1"],\
                                    frame["metrics"]["vif_scale2"],\
                                    frame["metrics"]["vif_scale3"]\
                                    ])
        csv_file = os.path.splitext(FileName)[0]+ '.csv'
        print (csv_file)
        with open(csv_file, 'w') as csvFile:
            csvFile.write(";".join(header))
            csvFile.write('\n')
            for line in csvData:
                csvFile.write(";".join(str(i) for i in line))
                csvFile.write('\n')

