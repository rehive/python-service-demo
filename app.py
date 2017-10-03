import os

from flask import Flask, Response, request
from rehive import Rehive, APIException

API_TOKEN = os.environ.get('REHIVE_API_TOKEN', '')

app = Flask(__name__)
rehive = Rehive(API_TOKEN)


@app.route('/')
def index():

	return "Rehive Demo {}".format(API_TOKEN[:12])


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


if __name__ == "__main__":
	app.run() 