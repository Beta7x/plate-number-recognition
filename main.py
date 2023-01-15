from flask import Flask, jsonify, request, render_template
from flask_restx import Resource, Api,reqparse
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.datastructures import FileStorage
from keras.models import load_model
import keras_preprocessing
from keras_preprocessing import image
import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt
import os
import tensorflow as tf
from tensorflow import keras
import chatbot
import easyocr
from keras.preprocessing import image
import sys

app = Flask(__name__)
api = Api(app)
CORS(app)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///images.db"
db.init_app(app)

#tabel image
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.String, nullable=False)
    
with app.app_context():
        db.create_all()

@api.route('/image/all', methods=["GET"])
class ImageAll(Resource):
    def get(self):
        images = db.session.execute(db.select(Image).order_by(Image.id)).scalars()
        data = []
        for image in images:
            data.append({
               'id': image.id,
                'name': image.name,
                'created_at': image.created_at,
            })
        return (data)

from werkzeug.datastructures import FileStorage
uploadParser = api.parser()
uploadParser.add_argument('image', location='files', type=FileStorage, required=True)
@api.route('/image')
class ImageAPI(Resource):
    @api.expect(uploadParser)
    def post(self):
        args = uploadParser.parse_args()
        file = args['image']
        file.save("./file_images/" + file.filename)
        filename = file.filename
        today = datetime.today()
        tanggal = f'{today}'
        image = Image(name=filename, created_at=tanggal)
        db.session.add(image)
        db.session.commit()
        
        #AI MODEL
        model = load_model('best-model.h5')
        path = "./images_upload/" + filename
        img = image.load_img(path, target_size=(400, 400))
        WIDTH, HEIGHT = img.shape
        y_hat = model.predict(img.reshape(1,WIDTH,HEIGHT,3)).reshape(-1)
    
        top_x, 	top_y = int(y_hat[0]),int(y_hat[1])
        bottom_x, bottom_y = int(y_hat[2]),int(y_hat[3])
        
        cropped_img = img[top_y-10:bottom_y+10,top_x-1:bottom_x+10]
        print(top_x,bottom_x,top_y,bottom_y)
        
        reader=easyocr.Reader(['en'])
        
        output = reader.readtext(cropped_img)
        output
        
        return jsonify({"no_plat": output , 
                        "created_at" : tanggal,
                            "message" : "Data Image Berhasil diupload "})

chatbotParser = reqparse.RequestParser()
chatbotParser.add_argument('msg', type=str, help='Message', location='args')
@api.route('/getchatbot')
class Chatbot(Resource):
    @api.expect(chatbotParser)
    def get(self):
        args = chatbotParser.parse_args()
        msg = args['msg']
        return chatbot.chatbot_response(msg)


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/history')
def history():
    return render_template('histori.html')

@app.route('/chats')
def chats():
    return render_template('chats.html')


if __name__ == '__main__':
    app.run(host='', port=5000, debug=True)