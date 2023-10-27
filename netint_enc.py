


def encfunc(type_enc, ch_size, name, enc_index):

    asic_1080p = f' -map [out1] -c:v:0 h264_ni_logan_enc -enc {enc_index} -xcoder-params "enableAUD=1:frameRate=25:RcEnable=1:RcInitDelay=2000:bitrate=5000000:entropyCodingMode=1:gopPresetIdx=5:profile=4:flushGop=1" \
        -b:v 5M  -bufsize 5M -force_key_frames "expr:gte(t,n_forced*2)"   \
        -map a:0 -c:a:0 aac -b:a:0 128k -ac 2 -ar 48k \
        -f hls -start_number 0 -hls_time {ch_size} -hls_list_size 0 -hls_playlist_type vod -hls_segment_type mpegts  \
        -hls_flags independent_segments -strftime 1 -strftime_mkdir 1 -hls_segment_filename  {name}_1080/{name}_1080_%s.ts  -var_stream_map "v:0,a:0"  {name}_1080.m3u8 '

    cpu_1080p = f' -map [out1] -c:v:0 libx264  -sc_threshold 0 -preset:v superfast -threads 8 -x264-params "nal-hrd=cbr:force-cfr=1:bframes=3:profile=high" \
        -b:v 5M  -bufsize 5M  -maxrate 5M  -force_key_frames "expr:gte(t,n_forced*2)"    \
        -map a:0 -c:a:0 aac -b:a:0 128k -ac 2 -ar 48k \
        -f hls -start_number 0 -hls_time {ch_size} -hls_list_size 0 -hls_playlist_type vod -hls_segment_type mpegts    \
        -hls_flags independent_segments -strftime 1 -strftime_mkdir 1 -hls_segment_filename  {name}_1080/{name}_1080_%s.ts -var_stream_map "v:0,a:0"  {name}_1080.m3u8 '

    asic_720p = f' -map [out2] -c:v:1 h264_ni_logan_enc -enc {enc_index} -xcoder-params "enableAUD=1:frameRate=25:RcEnable=1:RcInitDelay=2000:bitrate=3000000:entropyCodingMode=1:gopPresetIdx=5:profile=2:flushGop=1" \
        -b:v 3M  -bufsize 3M -force_key_frames "expr:gte(t,n_forced*2)"    \
        -map a:0 -c:a:0 aac -b:a:0 128k -ac 2 -ar 48k \
        -f hls -start_number 0 -hls_time {ch_size} -hls_list_size 0 -hls_playlist_type vod -hls_segment_type mpegts    \
        -hls_flags independent_segments -strftime 1 -strftime_mkdir 1 -hls_segment_filename  {name}_720/{name}_720_%s.ts -var_stream_map "v:0,a:0"  {name}_720.m3u8 '

    cpu_720p = f' -map [out2] -c:v:1 libx264 -sc_threshold 0 -preset:v superfast -threads 4 -x264-params "nal-hrd=cbr:force-cfr=1:bframes=2:profile=main" \
        -b:v 3M  -bufsize 3M -force_key_frames "expr:gte(t,n_forced*2)"    \
        -map a:0 -c:a:0 aac -b:a:0 128k -ac 2 -ar 48k \
        -f hls -start_number 0 -hls_time {ch_size} -hls_list_size 0 -hls_playlist_type vod -hls_segment_type mpegts    \
        -hls_flags independent_segments -strftime 1 -strftime_mkdir 1 -hls_segment_filename  {name}_720/{name}_720_%s.ts -var_stream_map "v:0,a:0"  {name}_720.m3u8 '

    asic_540p = f' -map [out3] -c:v:2 h264_ni_logan_enc -enc {enc_index} -xcoder-params "enableAUD=1:frameRate=25:RcEnable=1:RcInitDelay=2000:bitrate=1800000:entropyCodingMode=1:gopPresetIdx=5:profile=2:flushGop=1" \
        -b:v 1800k  -bufsize 1800k -force_key_frames "expr:gte(t,n_forced*2)"    \
        -map a:0 -c:a:0 aac -b:a:0 96k -ac 2 -ar 48k \
        -f hls -start_number 0 -hls_time {ch_size} -hls_list_size 0 -hls_playlist_type vod -hls_segment_type mpegts    \
        -hls_flags independent_segments -strftime 1 -strftime_mkdir 1 -hls_segment_filename  {name}_540/{name}_540_%s.ts  -var_stream_map "v:0,a:0"  {name}_540.m3u8 '

    cpu_540p = f' -map [out3] -c:v:2 libx264 -sc_threshold 0 -preset:v superfast -threads 4 -x264-params "nal-hrd=cbr:force-cfr=1:bframes=2:profile=main" \
        -b:v 1800k  -bufsize 1800k -force_key_frames "expr:gte(t,n_forced*2)"    \
        -map a:0 -c:a:0 aac -b:a:0 96k -ac 2 -ar 48k \
        -f hls -start_number 0 -hls_time {ch_size} -hls_list_size 0 -hls_playlist_type vod -hls_segment_type mpegts    \
        -hls_flags independent_segments -strftime 1 -strftime_mkdir 1 -hls_segment_filename  {name}_540/{name}_540_%s.ts  -var_stream_map "v:0,a:0"  {name}_540.m3u8 '

    asic_360p = f' -map [out4] -c:v:3 h264_ni_logan_enc -enc {enc_index} -xcoder-params "enableAUD=1:frameRate=25:RcEnable=1:RcInitDelay=2000:bitrate=600000:entropyCodingMode=1:gopPresetIdx=2:profile=1:flushGop=1" \
        -b:v 600k -bufsize 600k -force_key_frames "expr:gte(t,n_forced*2)"    \
        -map a:0 -c:a:0 aac -b:a:0 80k -ac 2 -ar 48k \
        -f hls -start_number 0 -hls_time {ch_size} -hls_list_size 0 -hls_playlist_type vod -hls_segment_type mpegts    \
        -hls_flags independent_segments -strftime 1 -strftime_mkdir 1 -hls_segment_filename  {name}_360/{name}_360_%s.ts -var_stream_map "v:0,a:0"  {name}_360.m3u8 '

    cpu_360p = f' -map [out4] -c:v:3 libx264 -sc_threshold 0 -preset:v superfast -threads 4 -x264-params "nal-hrd=cbr:force-cfr=1:bframes=0:profile=baseline" \
        -b:v 600k -bufsize 600k -force_key_frames "expr:gte(t,n_forced*2)"    \
        -map a:0 -c:a:0 aac -b:a:0 80k -ac 2 -ar 48k \
        -f hls -start_number 0 -hls_time {ch_size} -hls_list_size 0 -hls_playlist_type vod -hls_segment_type mpegts    \
        -hls_flags independent_segments -strftime 1 -strftime_mkdir 1 -hls_segment_filename  {name}_360/{name}_360_%s.ts  -var_stream_map "v:0,a:0"  {name}_360.m3u8 '


    if type_enc == 'hw':
        return asic_1080p,asic_720p,asic_540p,asic_360p
    elif type_enc == 'sw':
        return cpu_1080p,cpu_720p,cpu_540p,cpu_360p














