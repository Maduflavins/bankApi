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



class Transfer(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        to       = postedData["to"]
        money = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)

        cash = amountOwned(username)

        if cash<= 0:
            return jsonify(generateReturnDictionary304, "you are out of money, please add money or take a loan")

        if not UserExist(to):
            return jsonify(generateReturnDictionary(301, "Receiver username is invalis"))


        cash_from = amountOwned(username)
        cash_to = amountOwned(to)
        bank_cash = amountOwned("BANK")

        updateAccount("BANK", bank_cash+1)
        updateAccount(to, cash_to + money - 1)
        updateAccount(username, cash_from - money)

        return jsonify(generateReturnDictionary(200, "Amount Transfered successfully"))


class Balance(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)

        retJson = users.find({
            "Username": username
        }, {
            "Password": 0,
            "_id": 0
        })[0]

        return jsonify(retJson)


class TakeLoan(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money    = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)
        
        cash = amountOwned(username)
        debt = updateDebt(username)

        updateAccount(username, cash+money)
        updateDebt(username, debt + money)

        return jsonify(generateReturnDictionary(200, "Loan added to your account"))



class PayLoan(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)

        
        cash = amountOwned(username)

        if cash < money:
            return jsonify(generateReturnDictionary(303, "not enough cash in your account"))

         debt = userDebt(username)

         updateAccount(username, cash - money)
         updateDebt(username, debt - money)

         return jsonify(generateReturnDictionary(200, "you have successfully paid your loan"))



api.add_resource(Register, '/register')
api.add_resource(Add, '/add')
api.add_resource(Transfer, '/transfer')
api.add_resource(Balance, '/balance')
api.add_resource(TakeLoan, '/takeloan')
api.add_resource(PayLoan, '/payloan')


if __name__ == "__main__":
    app.run(host='0.0.0.0')