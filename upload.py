from flask import Flask, request, jsonify, Response
import os, hashlib, datetime, json
import extr_func


UPLOAD_FOLDER = '/content/imports'
ALLOWED_EXTENSIONS = set(['ts', 'mp4', 'mkv', 'mov'])
JSON_FOLDER = '/content/imports'
chunk_store = '/content/videos'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 * 1024
app.config['JSON_FOLDER'] = JSON_FOLDER
app.config['JSON_AS_ASCII'] = False


def SaveJson(data, filename):
    jsonfile = filename.rsplit('.', 1)[0]
    fullpath = os.path.join(app.config['JSON_FOLDER'], f'{jsonfile}.json')
    try:
        with open(fullpath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            return True
    except Exception as e:
        print(f"An error occurred while saving the data to {filename}: {e}")
        return False

def logging(type_log):

    current_date_time = datetime.datetime.now()
    formatted_date = current_date_time.strftime("%Y-%m-%d")
    log_filename = f"http_ft_{formatted_date}.log"

    log_directory = '/var/log/http_ft'
    os.makedirs(log_directory, exist_ok=True)

    with open(f'{log_directory}/{log_filename}', 'a') as log_file:
        log_file.write(f'{type_log} {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC, CALL FROM: {request.headers.get("X-Real-IP")}, Body: {list(request.form.items())}, File: {request.files.getlist("file")[0].filename} \n')


def can_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def get_extension(filename):
    return filename.rsplit('.', 1)[1]

@app.route('/upload', methods=['POST'])
def upload_files():

#    print(f'\nBody: {list(request.form.items())}\n')
#    print(f'Headers:\n{request.headers}')
#    print(f'\nFile: {request.files.getlist("file")[0].filename}\n')

    required_variables = ['hash', 'profiles', 'out_file', 'file', 'project']
    missing_variables = []
    for var in required_variables:
        if var not in request.form and var not in request.files:
            missing_variables.append(var)
    if missing_variables:
            logging('E')
            return Response(
                json.dumps({'type_service' : 'uploader', 'error': 'Missing in POST request: ' + ', '.join(missing_variables)}),
                status=400,
                mimetype='application/json'
            )

    hash_value = request.form.get('hash')
    profiles = request.form.get('profiles')
    out_file = request.form.get('out_file')
    project = request.form.get('project')

    files = request.files.getlist('file')

    content_range = request.headers.get('Content-Range')
    if content_range:
        parts = content_range.replace('bytes ', '').split('/')[0].split('-')
        start, end = map(int, parts) if len(parts) == 2 else (int(parts[0]), int(parts[0]))
        total = int(content_range.split('/')[1]) if '/' in content_range else None

    else:
        return Response(
                json.dumps({'type_service' : 'uploader', 'status': 'error', 'description': 'Missing Content-Range header for chunked upload.'}),
                status=400,
                mimetype='application/json'
            )
 
    chunk = request.files['file'].read()

    responses = []

    for file in files:
        filename = file.filename.replace(' ', '_')

        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}.part')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if start == 0 and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        if '.' not in filename or filename.rsplit('.', 1)[1] == '':
            logging('E')
            response = {
                'type_service' : 'uploader',
                'filename': filename,
                'status': 'error',
                'description': 'File does not have an extension.'
            }
            responses.append(response)
            continue

        extension = get_extension(filename)

        if allowed_file(filename):

            with open(os.path.join(temp_file_path), 'ab') as t_filepath:
                t_filepath.seek(start)
                t_filepath.write(chunk)

                response = {
                        'type_service' : 'uploader',
                        'filename': filename,
                       'description': f'Data {start} - {end} of {total} uploaded successfully.'
                        }
            if end >= total or end == total - 1:
                os.rename(temp_file_path, filepath)

                scan_result, scan_message = extr_func.checkScan(filepath)

                if scan_result == "Error":
                    logging('E')
#                    os.remove(filepath)
                    response = {
                        'type_service' : 'uploader',
                        'filename': filename,
                        'status': 'error',
                        'description': scan_message
                    }
                    responses.append(response)
                    continue

                checksum = hashlib.md5()
                with open(filepath, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        checksum.update(chunk)
                if checksum.hexdigest() != hash_value:
                    logging('E')
                    response = {
                        'type_service' : 'uploader',
                        'filename': filename,
                        'uploaded': f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC',
                        'hash': checksum.hexdigest(),
                        'received_hash': hash_value,
                        'status': 'error',
                    }
                elif can_int(profiles) is False:
                    logging('E')
                    response = {
                        'type_service' : 'uploader',
                        'filename': filename,
                        'uploaded': f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC',
                        'hash': checksum.hexdigest(),
                        'received_hash': hash_value,
                        'status': 'error',
                        'description': f'Wrong value for profiles: {profiles}, should int 1-5'
                    }
                elif 1 > int(profiles) or int(profiles) > 5:
                    logging('E')
                    response = {
                        'type_service' : 'uploader',
                        'filename': filename,
                        'uploaded': f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC',
                        'hash': checksum.hexdigest(),
                        'received_hash': hash_value,
                        'status': 'error',
                       'description': f'Wrong numblers for profiles: {profiles}, should be 1-5'
                    }
                else:
                    logging('I')
                    response = {
                        'type_service' : 'uploader',
                        'filename': filename,
                        'uploaded': f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC',
                        'hash': checksum.hexdigest(),
                        'received_hash': hash_value,
                        'profiles': profiles,
                        'status': 'ok',
                        'description': f'File received.',
                        'out_file': out_file,
                        'project': project
                    }

        else:
            logging('E')
            response = {
                'type_service' : 'uploader',
                'filename': filename,
                'status': 'error',
                'description': f'File extension {extension} not allowed! [mp4, ts, mkv, mov]'
            }
        responses.append(response)


    if 'hash' in responses[0] and responses[0]['status'] == 'ok':
        SaveJson(responses, filename)
    response_json = json.dumps(responses, ensure_ascii=False)
    return Response(response_json, mimetype='application/json')


#if __name__ == '__main__':
#    app.run(debug=False, host='127.0.0.1', port=8000)

