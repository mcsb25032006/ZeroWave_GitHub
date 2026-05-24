import os
import sys
from flask import Flask, request

from dotenv import load_dotenv

sys.path.insert(1, '/ussd_response')

from ussd_response.ai_response import autogenerate_tips_response
from ussd_response.sms_resposne import send_message

app = Flask(__name__)

@app.route("/ussd", methods = ['POST'])
def ussd():
  # Read the variables sent via POST from our API
  session_id   = request.values.get("sessionId", None)
  serviceCode  = request.values.get("serviceCode", None)
  phone_number = request.values.get("phoneNumber", None)
  text         = request.values.get("text", "default")

  # user_response = text.split('*')

  if text      == '':
      # This is the first request. Note how we start the response with CON
      response  = "CON Welcome to ZeroWave, Turning Waste to Energy \n"
      response += "1. Register \n"
      response += "2. ZeroTokens \n"
      response += "3. Community \n"
      response += "4. Locate Stations \n"
      response += "5. Get Tips & Alerts \n"
      response += "6. Report \n"
      response += "7. About ZeroWave \n"

  elif text    == '1':
      # Business logic for first level response
      response  = "CON Enter phone number: \n"
    #   response  = "CON Enter Full Names"

  elif text == "2":
    response = "CON Get to know your ZeroTokens \n"
    response += "1. Check Token Balance \n"
    response += "2. Redeem Tokens \n"
    response += "3. Earn More Tokens \n"


  elif text    == '2*3':
      response = f"END You will recieve a message shortly {send_message(phone_number, 'Your Points have been Redeemed Sucessfully')}"


  elif text    == '3':
      response = "CON Join ZeroWave Communities \n"
      response += "1. List all Communities \n"
      response += "2. Create a Community \n"
      response += "3. Communities nearby \n"



  elif text    == '4':
      response = "END ZeroWave Waste stations are located at www.zerowave.co.ke/stations"



  elif text    == '5':
      response = f"END You will recieve a message shortly {send_message(phone_number, autogenerate_tips_response())}"



  elif text   == '6':
      response = "CON Report an issue \n"
      response += "1. Report illegal dumping \n"
      response += "2. Report equipment malfunction \n"
      response += "3. Other issues \n"



  elif text    == '7':
    response = "END Transform your waste into valuable energy and earn rewards while saving the planet. Join the Sustainability Revolution. \nVisit www.zerowave.co.ke"


  # Send the response back to the API
  return response

if __name__ == '__main__':
    app.run(debug=True, port="8000")