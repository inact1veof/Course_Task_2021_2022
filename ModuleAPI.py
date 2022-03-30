import flask
from flask import Flask
from flask_restful import Api, Resource, reqparse
import random
import Distributor
app = Flask(__name__)
api = Api(app)

class Action(Resource):
    def get(self, datatype,FROM, content, timestamp = 0, condition = ''):
        return Distributor.getData(datatype,FROM,content,timestamp,condition)
    def post(self, datatype, TO,content,link, timestamp = 0):
        return Distributor.addData(datatype, TO, content, timestamp, link)
    def put(self, datatype, FROM, new_value, content = [], timestamp = 0):
        return Distributor.updateData(datatype, FROM, new_value, content, timestamp)
    def delete(self, datatype, FROM, identifier, content = []):
        return Distributor.remove(datatype, FROM, identifier, content)

if __name__=='__main__':
    app.run(debug=True)