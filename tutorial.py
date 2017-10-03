"""
This is a step by step guide to implementing the code found in app.py.

The code functions as a mini web service using flask as the framework and
gunicorn as the server (in heroku).
"""


# Setup
# ------------------------------------------------------------------------------
# 1. Ensure unverified users can have transactions
# 2. Setup a currency
# 3. Change to demo directory
# 4. Setup virtual env:
# 	a. `conda create -n rehive-sdk-demo python=3.6`
#	b. `source activate rehive-sdk-demo`
#   c. `pip install rehive`, `pip install flask`
# ------------------------------------------------------------------------------

# Step 1
# ------------------------------------------------------------------------------
# Import rehive SDK, set an api token and instantiate the rehive and flask 
# classes.
# ------------------------------------------------------------------------------

from flask import Flask, Response, request
from rehive import Rehive, APIException

API_TOKEN = ''

app = Flask(__name__)
rehive = Rehive(API_TOKEN)


# Step 2
# ------------------------------------------------------------------------------
# Add a webhook request endpoint
# this will receive webhooks from Rehive and automatically:
# 	1. Check if it is a complete credit transaction
#   2. Get the user's savings account.
#   3. Create a transfer to to the account
# ------------------------------------------------------------------------------

@app.route('/webhook/transaction/', methods=['POST'])
def webhook_transaction():
	content = request.get_json(silent=True)

	tx_type = content['data']['tx_type']
	source_transaction = content['data']['source_transaction']
	status = content['data']['status']
	amount = content['data']['amount']
	account_reference = content['data']['account']
	currency_code = content['data']['currency']['code']
	user_identifier = content['data']['user']['identifier']

	if status == "Complete" and source_transaction is None:
		accounts = rehive.admin.accounts.get(
			filters={"name": "savings", "user": user_identifier})

		if len(accounts) > 0:
			credit_account_reference = accounts[0]['reference']
		else:
			credit_account = rehive.admin.accounts.create(
			    name="savings",
			    primary=False,
			    user=user_identifier
			)

			credit_account_reference = account['reference']

		transaction = rehive.admin.transactions.create_transfer(
			user=user_identifier,
			recipient=user_identifier,
			debit_account=account_reference,
			credit_account=credit_account_reference,
			currency=currency_code,
			amount=int((10 * amount) / 100)
		)

		print(transaction)

	return Response("{'status':'success'}", status=200, 
		mimetype='application/json')


# Step 3
# ------------------------------------------------------------------------------
# 1. Create project on heroku (rehive-python-sdk-demo)
# 2. Deploy to Heroku
# 	a. $ heroku login 
# 	b. $ heroku git:remote -a rehive-python-sdk-demo
# 	c. $ git add. 
# 	d. $ git commit -m "commit message"
#	e. $ git push heroku master
# 	f. $ heroku config:set REHIVE_API_TOKEN={token}
# 3. Site can be found at:
#	a. https://rehive-python-sdk-demo.herokuapp.com/
# 4. Add webhooks
#	b. https://rehive-python-sdk-demo.herokuapp.com/webhook/transaction/'
#	c. credit

# ------------------------------------------------------------------------------