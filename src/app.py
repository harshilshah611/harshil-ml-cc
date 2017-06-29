"""
Flask Documentation:     http://flask.pocoo.org/docs/
Flask-SQLAlchemy Documentation: http://flask-sqlalchemy.pocoo.org/
SQLAlchemy Documentation: http://docs.sqlalchemy.org/
FB Messenger Platform docs: https://developers.facebook.com/docs/messenger-platform.

This file creates your application.
"""

import os

import flask
import requests
from flask_sqlalchemy import SQLAlchemy


FACEBOOK_API_MESSAGE_SEND_URL = (
    'https://graph.facebook.com/v2.6/me/messages?access_token=%s')

app = flask.Flask(__name__)

# TODO: Set environment variables appropriately.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['FACEBOOK_PAGE_ACCESS_TOKEN'] = os.environ[
    'FACEBOOK_PAGE_ACCESS_TOKEN']
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mysecretkey')
app.config['FACEBOOK_WEBHOOK_VERIFY_TOKEN'] = 'mysecretverifytoken'


db = SQLAlchemy(app)



senders = {}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Free form address for simplicity.
    full_address = db.Column(db.String, nullable=False)

    # Connect each address to exactly one user.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False)
    # This adds an attribute 'user' to each address, and an attribute
    # 'addresses' (containing a list of addresses) to each user.
    user = db.relationship('User', backref='addresses')

class TodoList(db.Model):
    senderId = db.Column(db.String(30), primary_key = True)
    listId = db.Column(db.Integer, primary_key = True)
    data = db.Column(db.String(100))
    status = db.Column(db.String(10))

    def __init__(self, a,b,c,d):
        self.senderId = a
        self.listId = b
        self.data = c
        self.status = d

@app.route('/')
def index():
    """Simple example handler.

    This is just an example handler that demonstrates the basics of SQLAlchemy,
    relationships, and template rendering in Flask.

    """
    # Just for demonstration purposes
    for user in User.query:  #
        print 'User %d, username %s' % (user.id, user.username)
        for address in user.addresses:
            print 'Address %d, full_address %s' % (
                address.id, address.full_address)

    # Render all of this into an HTML template and return it. We use
    # User.query.all() to obtain a list of all users, rather than an
    # iterator. This isn't strictly necessary, but just to illustrate that both
    # User.query and User.query.all() are both possible options to iterate over
    # query results.
    return flask.render_template('index.html', users=User.query.all())


@app.route('/fb_webhook', methods=['GET', 'POST'])
def fb_webhook():
    """This handler deals with incoming Facebook Messages.

    In this example implementation, we handle the initial handshake mechanism,
    then just echo all incoming messages back to the sender. Not exactly Skynet
    level AI, but we had to keep it short...

    """
    # Handle the initial handshake request.
    if flask.request.method == 'GET':
        if (flask.request.args.get('hub.mode') == 'subscribe' and
            flask.request.args.get('hub.verify_token') ==
            app.config['FACEBOOK_WEBHOOK_VERIFY_TOKEN']):
            challenge = flask.request.args.get('hub.challenge')
            return challenge
        else:
            print 'Received invalid GET request'
            return ''  # Still return a 200, otherwise FB gets upset.

    # Get the request body as a dict, parsed from JSON.
    payload = flask.request.json

    # TODO: Validate app ID and other parts of the payload to make sure we're
    # not accidentally processing data that wasn't intended for us.

    # Handle an incoming message.
    # TODO: Improve error handling in case of unexpected payloads.
    for entry in payload['entry']:
        for event in entry['messaging']:
            if 'message' not in event:
                continue
            message = event['message']
            # Ignore messages sent by us.
            if message.get('is_echo', False):
                continue
            # Ignore messages with non-text content.
            if 'text' not in message:
                continue
            sender_id = event['sender']['id']
            message_text = message['text']
            task = message_text.split()[0].lower()
            rest_message = ' '.join(message_text.split()[1:])
            request_url = FACEBOOK_API_MESSAGE_SEND_URL % (
                app.config['FACEBOOK_PAGE_ACCESS_TOKEN'])
            #Command : LIST
            if task=='list':
                try:
                    if str(sender_id) not in senders:
                        requests.post(request_url,
                                      headers={'Content-Type': 'application/json'},
                                      json={'recipient': {'id': sender_id},
                                            'message': {'text': "List Empty. Looks Like you are a new User"}})
                    else:
                        Items = TodoList.query.filter_by(senderId = str(sender_id)).all()
                        requests.post(request_url,
                                      headers={'Content-Type': 'application/json'},
                                      json={'recipient': {'id': sender_id},
                                            'message': {'text': "Items you have on the To-Do List are."}})
                        for item in Items:
                            if item.status == 'N':
                                requests.post(request_url,
                                              headers={'Content-Type': 'application/json'},
                                              json={'recipient': {'id': sender_id},
                                                    'message': {'text': str(item.listId)+ ".   " + item.data}})
                except:
                    requests.post(request_url,
                              headers={'Content-Type': 'application/json'},
                              json={'recipient': {'id': sender_id},
                                    'message': {'text': "Try the folowing commands\n List : Get all the To-do Items \n Add : Add a new To-do Item \n Done : Get all the check items \n Check : Check off an item by itemid"}})
            #Command : Done
            elif task == 'done':
                try:
                    if str(sender_id) not in senders:
                        requests.post(request_url,
                                      headers={'Content-Type': 'application/json'},
                                      json={'recipient': {'id': sender_id},
                                            'message': {'text': "List Empty. Looks like you are a new User"}})
                    else:
                        Items = TodoList.query.filter_by(status = "Y").all()
                        requests.post(request_url,
                                      headers={'Content-Type': 'application/json'},
                                      json={'recipient': {'id': sender_id},
                                            'message': {'text': "Items you have checked are."}})
                        for item in Items:
                            if item.status == 'Y':
                                requests.post(request_url,
                                              headers={'Content-Type': 'application/json'},
                                              json={'recipient': {'id': sender_id},
                                                    'message': {'text': str(item.listId)+ ".  " + item.data}})
                except:
                    requests.post(request_url,
                              headers={'Content-Type': 'application/json'},
                              json={'recipient': {'id': sender_id},
                                    'message': {'text': "Try the folowing commands\n List : Get all the To-do Items \n Add : Add a new To-do Item \n Done : Get all the check items \n Check : Check off an item by itemid"}})
            #Command : Add
            elif task == "add":
                try:
                    if str(sender_id) not in senders:
                        senders[str(sender_id)] = 1
                        listId = 1
                    else:
                        listId = senders[sender_id] + 1
                        senders[sender_id] += 1
                    
                    row = TodoList(str(sender_id), listId, rest_message, "N")
                    db.session.add(row)
                    db.session.commit()
                    requests.post(request_url,
                                  headers={'Content-Type': 'application/json'},
                                  json={'recipient': {'id': sender_id},
                                        'message': {'text': rest_message+ " added to the list"}})
                except:
                    requests.post(request_url,
                              headers={'Content-Type': 'application/json'},
                              json={'recipient': {'id': sender_id},
                                    'message': {'text': "Try the folowing commands\n List : Get all the To-do Items \n Add : Add a new To-do Item \n Done : Get all the check items \n Check : Check off an item by itemid"}})
            #Command : Check
            elif task == "check":
                try:       
                    if str(sender_id) not in senders:
                        requests.post(request_url,
                                      headers={'Content-Type': 'application/json'},
                                      json={'recipient': {'id': sender_id},
                                            'message': {'text': "List Empty. Looks like you are a new User"}})
                    else:
                        Items = TodoList.query.filter_by(senderId = str(sender_id)).all()
                        for item in Items:
                            if item.listId == int(rest_message):
                                item.status = 'Y'
                                data = item.data
                                db.session.commit()
                        requests.post(request_url,
                                  headers={'Content-Type': 'application/json'},
                                  json={'recipient': {'id': sender_id},
                                        'message': {'text': data+" checked"}})
                except:
                    requests.post(request_url,
                              headers={'Content-Type': 'application/json'},
                              json={'recipient': {'id': sender_id},
                                    'message': {'text': "Try the folowing commands\n List : Get all the To-do Items \n Add : Add a new To-do Item \n Done : Get all the check items \n Check : Check off an item by itemid"}})
            #Default
            else:
                requests.post(request_url,
                              headers={'Content-Type': 'application/json'},
                              json={'recipient': {'id': sender_id},
                                    'message': {'text': "Try the folowing commands\n List : Get all the To-do Items \n Add : Add a new To-do Item \n Done : Get all the check items \n Check : Check off an item by itemid"}})

    # Return an empty response.
    return ''

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)
