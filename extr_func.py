
import json, subprocess, datetime, os, shutil, time, configparser, shutil, requests


def read_config(project):
    config = configparser.ConfigParser()
    config.read('/etc/trans_sol/distr.conf')
    elements = []
    if project in config:
        for key in config[project]:
            elements.append(config[project][key])
        return elements
    else:
        return None


def resource_ch():
    enc_load = ["/usr/local/bin/ni_rsrc_mon_logan -o json1"]
    datajs = subprocess.getoutput(enc_load)
    start_index = datajs.find('{'); end_index = datajs.rfind('}') + 1
    res = json.loads(datajs[start_index:end_index])
    enc1_load = res["encoders"][0]["LOAD"]
    enc2_load = res["encoders"][1]["LOAD"]
    if int(enc1_load) <= 57:
        return 0, 'hw'
    elif int(enc1_load) >= 56 and int(enc2_load) <= 56:
        return 1, 'hw'
    elif int(enc1_load) >= 56 and int(enc2_load) >= 56:
        return "cpu", "sw"


def checkScan(input_file):
    mediainfo_cmd = f'/usr/bin/mediainfo --Output=JSON "{input_file}"'
    try:
        mediajson_str = subprocess.check_output(mediainfo_cmd, shell=True, text=True)
        mediajson = json.loads(mediajson_str)
    except subprocess.CalledProcessError as e:
        return "Error", f"An error occurred while running mediainfo: {e}"

    if 'track' not in mediajson.get("media", {}) or len(mediajson["media"]["track"]) < 2:
        return "Error", "No video or audio track found in the file."

    try:
        video_track = next((track for track in mediajson["media"]['track'] if track["@type"] == 'Video'), None)
        audio_track = next((track for track in mediajson["media"]['track'] if track["@type"] == 'Audio'), None)

        if not video_track or not audio_track:
            return "Error", "The file is missing a video or audio track."

        if video_track['Format'] == 'HEVC':
            return 'hevc', 'unk_'
        if video_track['ScanType'] == 'Progressive':
            return 'p', video_track['Sampled_Height']
        elif video_track['ScanType'] == 'Interlaced':
            return 'i', video_track['Sampled_Height']
        elif video_track['ScanType'] == 'MBAFF':
            return 'i', video_track['Sampled_Height']
    except (KeyError, IndexError) as e:
        return "Error", f"Error parsing media info: {e}"

    return "Error", "Unsupported video format or scan type."


def ScanType(type_scan, in_file, asic):
    decoder_i = f' -i {in_file}'
    decoder_p = f' -dec {asic} -c:v h264_ni_logan_dec -i {in_file} '
    decoder_h = f' -dec {asic} -c:v h265_ni_logan_dec -i {in_file} '
    if type_scan == "p":
        return decoder_p
    elif type_scan == "hevc":
        return decoder_h
    else:
        return decoder_i


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

    s_fhd =  f'{nl}#EXT-X-STREAM-INF:BANDWIDTH=6000000,RESOLUTION=1920x1080,CODECS="avc1.420028,mp4a.40.2"{nl}{name}_1080.m3u8{nl}'
    s_hd  =  f'{nl}#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1280x720,CODECS="avc1.42001f,mp4a.40.2"{nl}{name}_720.m3u8{nl}'
    s_sd  =  f'{nl}#EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION=960x540,CODECS="avc1.42001f,mp4a.40.2"{nl}{name}_540.m3u8{nl}'
    s_ssd =  f'{nl}#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1.42001e,mp4a.40.2"{nl}{name}_360.m3u8{nl}'
    s_sssd = f'{nl}#EXT-X-STREAM-INF:BANDWIDTH=400000,RESOLUTION=416x234,CODECS="avc1.42001e,mp4a.40.2"{nl}{name}_234.m3u8{nl}'

    proflink = [s_fhd, s_hd, s_sd, s_ssd,s_sssd]
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



def sync_hls(hls_files, project, retries=1):
    remote_hosts = read_config(project)
    if not remote_hosts:
        print("Missing remote hosts in conf file!")
        return 1
    for index, remote_path in enumerate(remote_hosts):
        for attempt in range(retries + 1):
            command = f"cd /content/processing/{hls_files} && /usr/bin/rsync -a . rsync://{remote_path}"
            try:
                result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                print(f"Synced with {remote_path}")
                break
            except subprocess.CalledProcessError as e:
                print(f"Attempt {attempt+1} for {remote_path} failed: {e.stderr}")
                if attempt == retries:
                    return e.returncode
                time.sleep(2)
            except Exception as e:
                print(f"Unexpected error: {e}")
                return 1
        else:
            print("All attempts failed.")
            return 1

    print('All CDN hosts synced!')
    shutil.rmtree(os.path.join('/content/processing', hls_files))
    print(f"Directory /content/processing/{hls_files} is deleted after last host synced.")
    return 0


def CallForResult(type_service, project, description, out_file, hash_sum, cdn_path=None):
    config = configparser.ConfigParser()
    config.read('/etc/trans_sol/distr.conf')
    if project in config:
        uri = config['endpoints'][project]

    payload = {
        'type_service': type_service,
        'project': project,
        'description': description,
        'hash_sum': hash_sum,
        'out_file': out_file,
        'status': 'ok'
    }
    if cdn_path is not None:
        payload['cdn_path'] = cdn_path

    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            response = requests.post(uri, json=payload, verify=True)
            if response.ok:
                print(f"Call to {project} API Success for video {out_file}.")
                return f"Call to {project} API Success"
            else:
                print(f"Attempt {attempt + 1} of {max_attempts} failed with status code {response.status_code}")
        except requests.RequestException as e:
            print(f"Request exception on attempt {attempt + 1}: {e}")
            if attempt >= max_attempts - 1:
                return f"Error after multiple attempts to {project} API: {e}"

        if attempt < max_attempts - 1:
            time.sleep(2)
        else:
            print("Max attempts reached, no more retries.")


