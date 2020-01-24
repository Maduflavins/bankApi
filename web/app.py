from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt


app = Flask(__name__)

api = Api(app)


client = MongoClient("mongodb://db:27017")
db = client.BankApi

users = db["Users"]


def UserExist(username):
    if users.find({"Username": username}).count()==0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
                "status": "301",
                "message": "Invalid Username"
            }
            return jsonify(retJson)
        
        hashed_pw = bcrypt.hashed_pw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            "username": username,
            "Password": hashed_pw,
            "Credit": 0,
            "Debt": 0
        })

        retJson = {
            "status": 200,
            "message": "You succssefully signed up"
        }

        return jsonify(retJson)
    

def verifyPW(username, password):
    if not UserExist(username):
        return False
    
    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    if bcrypt.haspw(password.encode('utf8'), hashed_pw)==hashed_pw:
        return True
    else:
        return False
    
def amountOwned(username):
    balance = users.find({
        "Username": username
    })[0]["Crdeit"]

    return balance


def userDebt(username):
    debt = users.find({
        "Username": username
    })[0]["Debt"]
    return debt



def generateReturnDictionary(status, message):
    retJson = {
        "status": status,
        "message": message
    }
    return retJson


def verifyCredentials(username, password):
    if not UserExist(username):
        return generateReturnDictionary(301, "Invalid Username"), True
    
    correct_pw = verifyPW(username, password)

    if not correct_pw:
        return generateReturnDictionary(302, "Incorrect Password"), True

    return None, False


def updateAccount(username, balance):
    users.update({
        "Username": username
    }, {
        "$set": {
            "Credit": balance
        }
    })


def updateDebt(username, balance):
    users.update({
        "Username": username
    }, {
        "$set":{
            "Debt": balance
        }
    })


 
class Add(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)
        
        if money <= 0:
            return jsonify(generateReturnDictionary(304, "The amount entered is invalid, amount must be greater than 0"))
        
        cash = amountOwned(username)
        money-=1
        bank_cash = amountOwned("BANK")
        updateAccount("Bank", bank_cash+1)
        updateAccount(username, cash+money)

        return jsonify(generateReturnDictionary(200, "Amount added successfully to account"))