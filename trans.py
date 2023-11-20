
import os, sys, subprocess, datetime
import extr_func, netint_enc


def init_trans(in_file, o_path, o_name, profiles):
    global input_file, out_path, adb_prof, asic_hw, enctp, sc_type, ffneint, decode, out_name

    input_file = in_file
    out_path = o_path
    out_name = o_name
    if not os.path.exists(out_path):
        os.makedirs(out_path)
        print(f'Directory does not exist, created: {out_path}')

    adb_prof = profiles
    asic_hw = extr_func.resource_ch()[0]
    enctp = extr_func.resource_ch()[1]
    sc_type = extr_func.checkScan(input_file)[0]

    if asic_hw == 'cpu':
        ffneint = "/etc/trans_sol/ffmpeg_cpu "
        decode = f' -i {input_file}'

    else:
        ffneint = "/root/FFmpeg/ffmpeg_netint "
        decode =  extr_func.ScanType(sc_type, input_file, asic_hw)


def profiles(prof: int):

    seg_time = 10
    v_size_1 = "1920:1080"
    v_size_2 = "1280:720"
    v_size_3 = "960:540"
    v_size_4 = "640:360"
    v_size_5 = "416:234"

    if 1 > prof or prof > 5:
        print(f'Wrong numblers for profiles: {prof} , should be 1-5'); exit()
    else:
        init_f = f' -filter_complex '
        profs_t = [f'[v1]scale={v_size_1},setdar=16/9,format=yuv420p[out1];',
                   f'[v2]scale={v_size_2},setdar=16/9,format=yuv420p[out2];',
                   f'[v3]scale={v_size_3},setdar=16/9,format=yuv420p[out3];',
                   f'[v4]scale={v_size_4},setdar=16/9,format=yuv420p[out4];',
                   f'[v5]scale={v_size_5},setdar=16/9,format=yuv420p[out5]']
        profs = "".join(profs_t[-prof:])
        tags_v = ['[v1]','[v2]','[v3]','[v4]','[v5]']
        vtags = "".join(tags_v[-prof:])
        splits = f'[v:0]yadif=0:-1:1,split={prof}{vtags};{profs}'
        enc_func = netint_enc.encfunc(enctp, seg_time, out_name, asic_hw)
        enc_f = "".join(enc_func[-prof:])
        return f'{init_f}"{splits}" {enc_f}'


def enc_process(minput_file, mout_path, o_name, madb_prof, project, file_hash):

    start_index = mout_path.find('/videos/')
    remote_path = mout_path[start_index:]
    print(f'Remote path: {remote_path}')
    loglevel = ' -loglevel quiet '
    init_trans(minput_file, mout_path, o_name, madb_prof)
    print(f'in={input_file}, out={out_path}, profiles={adb_prof},asic={asic_hw},type={enctp},scan={sc_type}')

    ff_cli = [f'cd {mout_path}; {ffneint} {decode} {loglevel} {profiles(adb_prof)}']

    try:
        extr_func.CallForResult('transcoder', project, 'The file received, starting transcoding.', o_name, file_hash)
        start_time = datetime.datetime.now().strftime("%H:%M:%S")
        print(f'Starting transcode process at {start_time} for file {minput_file}. ')
        result = subprocess.run(ff_cli, shell=True, check=True)

        if result.returncode == 0:
            result_status = 'success'
            extr_func.CallForResult('transcoder', project, 'The file is transcoded and proceeds for distribution.', o_name, file_hash)
            extr_func.move_files([minput_file, f'{os.path.splitext(minput_file)[0]}.json' ],f'/content/done/{datetime.datetime.now().strftime("%Y-%m-%d")}')
            extr_func.logging(start_time, datetime.datetime.now().strftime("%H:%M:%S"), input_file, out_path, adb_prof, result_status)
            print(f'Transcode process finish at {datetime.datetime.now().strftime("%H:%M:%S")} for file {minput_file}. ')
            extr_func.make_manifest(adb_prof, out_path, out_name)
            print(f'Start syncro for {o_name} at project {project}.')
            result_for_sync = extr_func.sync_hls(o_name, project)
            if result_for_sync == 0:
                extr_func.CallForResult('distribution', project, 'All CDN hosts synced!', o_name, file_hash, remote_path)
        else:
            result_status = 'error'
            extr_func.logging(start_time, datetime.datetime.now().strftime("%H:%M:%S"), input_file, out_path, adb_prof, result_status)
            extr_func.move_files([minput_file, f'{os.path.splitext(minput_file)[0]}.json' ],f'/content/errors/{datetime.datetime.now().strftime("%Y-%m-%d")}')

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        result_status = 'error'
        extr_func.logging(start_time, datetime.datetime.now().strftime("%H:%M:%S"), input_file, out_path, adb_prof, result_status)
        extr_func.move_files([minput_file, f'{os.path.splitext(minput_file)[0]}.json' ],f'/content/errors/{datetime.datetime.now().strftime("%Y-%m-%d")}')



