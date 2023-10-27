from flask import Flask, request, jsonify, Response
import os, hashlib, datetime, json
import extr_func


UPLOAD_FOLDER = '/content/imports'
ALLOWED_EXTENSIONS = set(['ts', 'mp4', 'mkv'])
JSON_FOLDER = '/content/imports'
chunk_store = '/content/videos'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024
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

def logging():

    current_date_time = datetime.datetime.now()
    formatted_date = current_date_time.strftime("%Y-%m-%d")
    log_filename = f"http_ft_{formatted_date}.log"

    log_directory = '/var/log/http_ft'
    os.makedirs(log_directory, exist_ok=True)

    with open(f'{log_directory}/{log_filename}', 'a') as log_file:
        log_file.write(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC, call from: {request.headers.get("X-Real-IP")} with: {request.form}\n')


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

    required_variables = ['hash', 'profiles', 'out_file', 'project']
    for var in required_variables:
        if var not in request.form:
            return Response(json.dumps({'error': f'Missing {var} in POST request'}), status=400, mimetype='application/json')

    logging()

    hash_value = request.form.get('hash')
    profiles = request.form.get('profiles')
    out_file = request.form.get('out_file')
    project = request.form.get('project')

    files = request.files.getlist('file')
    responses = []

    for file in files:
        filename = file.filename.replace(' ', '_')
        extension = get_extension(filename)

        if allowed_file(filename):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            md5_hash = hashlib.md5()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            if md5_hash.hexdigest() != hash_value:
                response = {
                    'filename': filename,
                    'uploaded': f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC',
                    'hash': md5_hash.hexdigest(),
                    'received_hash': hash_value,
                    'status': 'error',
                    'description': 'Wrong file checksum!'
                }
            elif can_int(profiles) is False:
                response = {
                    'filename': filename,
                    'uploaded': f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC',
                    'hash': md5_hash.hexdigest(),
                    'received_hash': hash_value,
                    'status': 'error',
                    'description': f'Wrong value for profiles: {profiles}, should int 1-4'
                }
            elif 1 > int(profiles) or int(profiles) > 4:
                response = {
                    'filename': filename,
                    'uploaded': f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC',
                    'hash': md5_hash.hexdigest(),
                    'received_hash': hash_value,
                    'status': 'error',
                    'description': f'Wrong numblers for profiles: {profiles}, should be 1-4'
                }
            else:
                scan, resol = extr_func.checkScan(filepath)
                response = {
                    'filename': filename,
                    'uploaded': f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC',
                    'hash': md5_hash.hexdigest(),
                    'received_hash': hash_value,
                    'profiles': profiles,
                    'status': 'ok',
                    'description': f'Video resolution: {resol}{scan}',
                    'out_file': out_file,
                    'project': project
                }
        else:
            response = {
                'filename': filename,
                'status': 'error',
                'description': f'File extension {extension} not allowed! [mp4, ts]'
            }

        responses.append(response)
    if 'hash' in responses[0] and responses[0]['status'] == 'ok':
        SaveJson(responses, filename)

    return Response(json.dumps(responses, ensure_ascii=False), mimetype='application/json')

#if __name__ == '__main__':
#    app.run(debug=False, host='127.0.0.1', port=8000)

