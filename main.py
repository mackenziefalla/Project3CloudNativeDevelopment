# This Code has been edited by Mackenzie Falla
# Cloud Native Development
# Skeleton given by Professor Ricardo De Andrade,
# I also looked to ChatGBT for help as well as the class TA.

import os
from flask import Flask, redirect, request, url_for, send_file, abort, jsonify, Response
from google.cloud import storage
import google.generativeai as genai
import io
import PIL
import base64
import json



genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Initialize Google Cloud Storage client
storage_client = storage.Client(project='project1-447922')   #connecting my project
bucket_name = os.environ.get("BUCKETNAME")      # Connecting my bucket 
bucket = storage_client.get_bucket(bucket_name)

ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'png'}     # allowed image types 

def generate_description(image):
    part = ["Give me a simple one line title and a one line description for this image", PIL.Image.open(image)] 
    genai_response = model.generate_content(part)
    # genai_response = model.generate_content("Tell me a story for a child",response)
    print(genai_response.text)
    lines = genai_response.text.split("\n")
    print(lines, len(lines))
    if len(lines) == 6:
        for line in lines:
            print(line)
        print(lines[2].split(":"))
        print(lines[4].split(":"))
        title = lines[2].split(":")[1]
        description = lines[4].split(":")[1]
    elif len(lines) == 4:
        for line in lines:
            print(line)
        print(lines[0].split(":"))
        print(lines[2].split(":"))
        title = lines[0].split(":")[1]
        description = lines[2].split(":")[1]
    elif len(lines) == 3:
        for line in lines:
            print(line)
        print(lines[0].split(":"))
        print(lines[2].split(":"))
        title = lines[0].split(":")[1]
        description = lines[2].split(":")[1]
    elif len(lines) == 5:
        for line in lines:
            print(line)
        print(lines[2].split(":"))
        print(lines[4].split(":"))
        title = lines[2].split(":")[1]
        description = lines[4].split(":")[1]   
    elif len(lines) == 2: 
        for line in lines:
            print(line)
        print(lines[0].split(":"))
        print(lines[1].split(":"))
        title = lines[0].split(":")[1]
        description = lines[1].split(":")[1]  
    else: 
        generate_description(image)


    # Data to be written
    dictionary = {
        "title": title,
        "description": description,
    }
 
    # Serializing json
    json_object = json.dumps(dictionary, indent=4)
    file_name = image.filename.split(".")[0]+".json"
 
    # Writing to sample.json
    with open(file_name, "w") as outfile:
        outfile.write(json_object)

    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)
    os.remove(file_name)

app = Flask(__name__) #app setup

def all_files():
    """Retrieves all images from the GCS bucket."""
    images = []
    all_bucket_files = storage_client.list_blobs(bucket_name)
    for file in all_bucket_files:
        if file.name.lower().endswith(('.jpeg', '.jpg', '.png')):
            images.append(file.name)
    print(f"Files in bucket: {images}")  # Debugging list of files
    return images

@app.route('/')
def index():
    """Home page with upload form and list of uploaded files."""
    index_html = """
    <html>
    <head><title>Upload Files</title></head>
    <body>
        <h1>Upload Image</h1>
        <form method="post" enctype="multipart/form-data" action="/upload">
            <div>
                <label for="file">Choose file to upload</label>
                <input type="file" id="file" name="form_file" accept="image/**">
            </div>
            <div>
                <button>Submit</button>
            </div>
        </form>
        <h2>Uploaded Files:</h2>
        <ul>
    """
       
    files = all_files()  # Fetch file list
    for file in files:
        index_html += f"<li><a href='/files/{file}'>{file}</a></li>"

    index_html += """
        </ul>
    </body>
    </html>
    """
    return index_html  

def allowed_file(filename):
   """Check if the file has an allowed extension."""
   return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=["POST"])
def upload():
   """Handles file upload and saves to the specified bucket."""
   file = request.files.get('form_file')
   if file and allowed_file(file.filename):
       blob = bucket.blob(file.filename)
       blob.upload_from_file(file)
       generate_description(file)
       return redirect(url_for('index'))
       return 'Invalid file type or upload failed', 400

@app.route('/files/<filename>')
def get_file(filename):
    file_name_1 = filename
    file_name = filename.split(".")[0]+".json"
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    print(blob)
    file_content = None
    with blob.open("r") as file_object:
        file_content = file_object.read()
    file_content = json.loads(file_content)
    print(file_content["title"], file_content["description"])
    html=f"""
    <body>
        <img src = '/images/{file_name_1}' width="25%">
        <br/>
        <p>title: {file_content["title"]}</p>
        <p>description: {file_content["description"]}</p>
    </body>
    """
    return html

@app.route('/images/<imagename>')
def get_image(imagename):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(imagename)
    file_data = blob.download_as_bytes()
    return Response(io.BytesIO(file_data), mimetype='image/jpeg')

if __name__ == '__main__': 
 app.run(host="localhost",port=4070, debug=True) 
 #I used port 4070 because 8080 was busy
