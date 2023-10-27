
import json, subprocess, datetime, os, shutil

def resource_ch():
    enc_load = ["/usr/local/bin/ni_rsrc_mon_logan -o json1"]
    datajs = subprocess.getoutput(enc_load)
    start_index = datajs.find('{'); end_index = datajs.rfind('}') + 1
    res = json.loads(datajs[start_index:end_index])
    enc1_load = res["encoders"][0]["LOAD"]
    enc2_load = res["encoders"][1]["LOAD"]
    if int(enc1_load) <= 50:
        return 0, 'hw'
    elif int(enc1_load) >= 50 and int(enc2_load) <= 50:
        return 1, 'hw'
    elif int(enc1_load) >= 50 and int(enc2_load) >= 50:
        return "cpu", "sw"


def checkScan(input_file):
    mediainfo = [f'/usr/bin/mediainfo --Output=JSON {input_file}']
    mediajson = json.loads(subprocess.getoutput(mediainfo))
    if mediajson["media"]['track'][1]['ScanType'] == 'Progressive':
        return 'p', mediajson["media"]['track'][1]['Sampled_Height']
    elif mediajson["media"]['track'][1]['ScanType'] == 'Interlaced':
        return 'i', mediajson["media"]['track'][1]['Sampled_Height']


def ScanType(type_scan, in_file, asic):
    decoder_i = f' -i {in_file}'
    decoder_p = f' -dec {asic} -c:v h264_ni_logan_dec -i {in_file} '
    if type_scan == "p":
        return decoder_p
    else:
        return decoder_i


def get_profiles(resol):
    if int(resol) >= 1080:
        return 4
    elif int(resol) >= 720 and int(resol) <= 1079:
        return 3
    elif int(resol) >= 520 and int(resol) <= 719:
        return 2
    else:
        return 1

def move_files(source_files, destination_directory):
    try:
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory)
        for source_file_path in source_files:
            filename = os.path.basename(source_file_path)
            destination_file_path = os.path.join(destination_directory, filename)
            shutil.move(source_file_path, destination_file_path)
            print(f"Job done '{filename}' moved successfully to '{destination_directory}'")
    except FileNotFoundError as e:
        print(f"Error: One of the files does not exist. Details: {e}")
    except PermissionError as e:
        print(f"Error: Insufficient permissions to move one of the files. Details: {e}")
    except Exception as e:
        print(f"An error occurred while moving the files: {e}")


def make_manifest(pro: int, dest_dir, name):
    nl = '\n'

    head = f'#EXTM3U{nl}#EXT-X-VERSION:6'

    s_fhd = f'{nl}#EXT-X-STREAM-INF:BANDWIDTH=6000000,RESOLUTION=1920x1080,CODECS="avc1.420028,mp4a.40.2"{nl}{name}_1080.m3u8{nl}'
    s_hd  = f'{nl}#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1280x720,CODECS="avc1.42001f,mp4a.40.2"{nl}{name}_720.m3u8{nl}'
    s_sd  = f'{nl}#EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION=960x540,CODECS="avc1.42001f,mp4a.40.2"{nl}{name}_540.m3u8{nl}'
    s_ssd = f'{nl}#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1.42001e,mp4a.40.2"{nl}{name}_360.m3u8{nl}'

    proflink = [s_fhd, s_hd, s_sd, s_ssd]
    prof_links = head+"".join(proflink[-pro:])

    with open(f'{dest_dir}/playlist.m3u8', 'w') as manifest:
        manifest.write(prof_links)
    print(f'Master manifest created for {pro} profiles.')
    print(f'#####################################################################')


def logging(start, end, infile, outfile, profiles, result=None):
    current_date_time = datetime.datetime.now()
    formatted_date = current_date_time.strftime("%Y-%m-%d")
    log_filename = f"trans_log_{formatted_date}.log"

    log_directory = '/content/logs/'
    os.makedirs(log_directory, exist_ok=True)

    with open(f'{log_directory}/{log_filename}', 'a') as log_file:
        log_file.write(f'{result}\tStart_time={start}\tEnd_time={end}\tin_file={infile}\tout_dir={outfile}\tprofiles={profiles}\n')


