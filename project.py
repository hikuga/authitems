from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Parent, Child
from flask import session as login_session
import random
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

import string

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Web client 1"


# Connect to Database and create database session
engine = create_engine('sqlite:///parentchild.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    #return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

def dict_xml(tag,d):
    elem = Element(tag)
    for k,v in d.items():
        child=Element(k)
        if isinstance(v, dict):
            child.text = tostring( dict_to_xml(tag, v))
        else:
            child.text = str(v)
        elem.append(child)
    return elem
    
def xmlfy(data):
    if isinstance(data, dict):
        return unescape(tostring(dict_xml('skishop', data)))
    if isinstance(data, list):
        elem=Element(tag)
        for subdata in data:
            elemsub=Element(tag)
            if isinstance(subdata, dict):
                elemsub=dict_xml(tag, subdata)
                elem.append(elemsub)
        return unescape(tostring(elem))

# JSON APIs to view Restaurant Information
@app.route('/skishop/<int:skishop_id>/items/JSON')
def skishopItemsJSON(skishop_id):
    restaurant = session.query(Parent).filter_by(id=skishop_id).one()
    items = session.query(Child).filter_by(
        parent_id=skishop_id).all()
    return jsonify(SkiItems=[i.serialize for i in items])


@app.route('/skishop/<int:skishop_id>/items/<int:item_id>/JSON')
def skishopItemJSON(skishop_id, item_id):
    Skishop_Item = session.query(Child).filter_by(id=item_id).one()
    return jsonify(SkishopItem=Skishop_Item.serialize)


@app.route('/skishop/JSON')
def skishopsJSON():
    skishops = session.query(Parent).all()
    return jsonify(skishops=[r.serialize for r in skishops])


# Show all skishops
@app.route('/')
@app.route('/skishop/')
def showSkishops():
    skishops = session.query(Parent).order_by(asc(Parent.name))
    return render_template('skishops.html', skishops=skishops)

# Create a new ski store


@app.route('/skishop/new/', methods=['GET', 'POST'])
def newSkishop():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newSkishop = Parent(name=request.form['name'])
        session.add(newSkishop)
        flash('New Ski store %s Successfully Created' % newSkishop.name)
        session.commit()
        return redirect(url_for('showSkishops'))
    else:
        return render_template('newSkishop.html')

# Edit a skishop

@app.route('/skishop/<int:skishop_id>/edit/', methods=['GET', 'POST'])
def editSkishop(skishop_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedSkishop = session.query(
        Parent).filter_by(id=skishop_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedSkishop.name = request.form['name']
            flash('Skishop Successfully Edited %s' % editedSkishop.name)
            return redirect(url_for('showSkishops'))
    else:
        return render_template('editSkishop.html', skishop=editedSkishop)


# Delete a skishop
@app.route('/skishop/<int:skishop_id>/delete/', methods=['GET', 'POST'])
def deleteSkishop(skishop_id):
    if 'username' not in login_session:
        return redirect('/login')
    skishopToDelete = session.query(
        Parent).filter_by(id=skishop_id).one()
    if request.method == 'POST':
        session.delete(skishopToDelete)
        flash('%s Successfully Deleted' % skishopToDelete.name)
        session.commit()
        return redirect(url_for('showSkishops', skishop_id=skishop_id))
    else:
        return render_template('deleteSkishop.html', skishop=skishopToDelete)

# Show a skistore contents


@app.route('/skishop/<int:skishop_id>/')
@app.route('/skishop/<int:skishop_id>/items/')
def showItems(skishop_id):
    skishop = session.query(Parent).filter_by(id=skishop_id).one()
    items = session.query(Child).filter_by(
        parent_id=skishop_id).all()
    return render_template('items.html', items=items, skishop=skishop)


# Create a new  item
@app.route('/skishop/<int:skishop_id>/items/new/', methods=['GET', 'POST'])
def newItem(skishop_id):
    if 'username' not in login_session:
        return redirect('/login')
    skishop = session.query(Parent).filter_by(id=skishop_id).one()
    if request.method == 'POST':
        newItem = Child(name=request.form['name'], description=request.form[
                           'description'], price=request.form['price'], attribute=request.form['attribute'], parent=skishop)
        session.add(newItem)
        session.commit()
        flash('New  %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showItems', skishop_id=skishop_id))
    else:
        return render_template('newItem.html', skishop_id=skishop_id)

# Edit a menu item


@app.route('/skishop/<int:skishop_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(skishop_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Child).filter_by(id=item_id).one()
    skishop = session.query(Parent).filter_by(id=skishop_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['attribute']:
            editedItem.attribute = request.form['attribute']
        session.add(editedItem)
        session.commit()
        print 'done editing'
        flash('Skishop Item Successfully Edited')
        return redirect(url_for('showItems', skishop_id=skishop_id))
    else:
        return render_template('editItem.html', skishop_id=skishop_id, item_id=item_id, item=editedItem)


# Delete a menu item
@app.route('/skishop/<int:skishop_id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(skishop_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    skishop = session.query(Parent).filter_by(id=skishop_id).one()
    itemToDelete = session.query(Child).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Skishop Item Successfully Deleted')
        return redirect(url_for('showItems', skishop_id=skishop_id))
    else:
        return render_template('deleteItem.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
