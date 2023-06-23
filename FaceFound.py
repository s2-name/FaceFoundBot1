import os
import face_recognition
import datetime
import numpy
from PIL import Image

from config import *

class FaceFound:
    def __init__(self, db, tmp_dir=None, save_dir=None):
        self.__db = db
        self.__tmp_dir = tmp_dir or "imgs"
        self.__save_dir = save_dir or os.path.join("server", "media")

    def add_face_in_db(self, img_path: str, source=None) -> bool:
        ''' encode an image with a face and add the face to the database.
            img_path - path to the image '''
        image = face_recognition.load_image_file(img_path)
        face_encoding = face_recognition.face_encodings(image)
        path_moved_img = self.__move_file(img_path)
        if self.__db.add_face(self.__encoding_FaceStr(face_encoding[0]), source, path_moved_img)[0]:
            return True
        else:
            return False

    def find_face(self, path_to_img: str) -> list:
        ''' Find the face in the database. Give her the path to the image file
            Returns a list with the found ID matches '''

        image = face_recognition.load_image_file(path_to_img)
        faces_encoding = face_recognition.face_encodings(image)

        list_of_matches = []

        faces_from_db = self.__db.get_faces()
        if faces_from_db[0]:
            for received_face in faces_encoding:
                for face_db in faces_from_db[1]:
                    decoded_face = self.__decoding_FaceStr(face_db[1])
                    a = face_recognition.compare_faces([decoded_face], received_face)[0]
                    if a:
                        list_of_matches.append(face_db[0])
        else:
            print(faces_from_db[1])

        return list_of_matches

    def __encoding_FaceStr(self, image_face_encoding) -> str:
        '''Encoding of the face_recognition.face_encodings result to a string to be saved in the database'''

        encoding__array_list = image_face_encoding.tolist()
        encoding_str_list = [str(i) for i in encoding__array_list]
        encoding_str = ','.join(encoding_str_list)
        return encoding_str

    def __decoding_FaceStr(self, encoding_str: str) -> numpy.ndarray:
        '''Decoding a string from a database to nndy ndarray'''

        dlist = encoding_str.strip(' ').split(',')
        dfloat = list(map(float, dlist))
        face_encoding = numpy.array(dfloat)
        return face_encoding

    def __move_file(self, img_path: str, new_size_ratio=IMG_COMPRESSION_RATIO, quality=90) -> str:
        ''' moves the file to the storage folder, compresses the size and encodes in jpg '''
        img = Image.open(img_path)
        img = img.resize((int(img.size[0] * new_size_ratio), int(img.size[1] * new_size_ratio)))
        other_path, filename = os.path.split(img_path)
        filename, ext = os.path.splitext(filename)
        new_filename = f"{SAVE_IMG_DIR}/{filename}.jpg"
        try:
            img.save(new_filename, quality=quality, optimize=True)
        except OSError:
            img = img.convert("RGB")
            img.save(new_filename, quality=quality, optimize=True)

        return new_filename




