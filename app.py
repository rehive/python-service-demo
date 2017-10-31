import os
from functools import wraps

from flask import Flask, Response, request, json
from rehive import Rehive, APIException

app = Flask(__name__)

# The Rehive admin API key used for the SDK.
API_TOKEN = os.environ.get('REHIVE_API_TOKEN', '')

# The webhook secret attached to the webhook in Rehive.
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', '')


def get_auth_token(request, name='secret'):
	"""
	Get the auth token from the AUTHORIZATION header.
	"""

    try:
        auth = request.headers['HTTP_AUTHORIZATION'].split()
    except KeyError:
        return None

    if auth and auth[0].lower() != name:
        return None

    if not auth[1]:
        return None

    return auth[1]


def authenticate(request):
	"""
	Return JSON indicating authorization is required.
	"""

    data = {'status':'error', 
            'message': 'Invalid webhook secret.'}

    return Response(json.dumps(data), status=403, mimetype='application/json')


def requires_auth(f):
	"""
	Wrapper for authentication. Checks that the correct webhook secret is 
	present in the authorization header.
	"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_auth_token(request)
        
        if not token or token != WEBHOOK_SECRET:
            return authenticate()

        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
	"""
	Home page for the service.
	"""

	return "Rehive Python Service Demo"


@app.route('/webhook/transaction/', methods=['POST'])
@requires_auth
def webhook_transaction():
	"""
	Webhook endpoint. This authenticates the webhook against the stored webhook 
	secret. If the received transaction passes the validation then a savings
	account is found/created for the user and a portion of the transaction 
	amount is transfered to the savings account.
	"""

	content = request.get_json(silent=True)

	source_transaction = content['data']['source_transaction']
	status = content['data']['status']
	amount = content['data']['amount']
	account_reference = content['data']['account']
	currency_code = content['data']['currency']['code']
	user_identifier = content['data']['user']['identifier']	

	if (status == "Complete" and source_transaction is None
			and amount > 10):
		rehive = Rehive(API_TOKEN)

		accounts = rehive.admin.accounts.get(
			filters={"name": "savings", 
					 "user": user_identifier}
		)

		try:
			savings_account = accounts[0]
		except KeyError:
			savings_account = rehive.admin.accounts.create(
			    name="savings",
			    primary=False,
			    user=user_identifier
			)

		transaction = rehive.admin.transactions.create_transfer(
			user=user_identifier,
			recipient=user_identifier,
			debit_account=account_reference,
			credit_account=savings_account['reference'],
			currency=currency_code,
			amount=int((10 * amount) / 100)
		)

	return Response(json.dumps({'status':'success'}), status=200, 
		mimetype='application/json')


# Run the falsk application
if __name__ == "__main__":
	app.run() 