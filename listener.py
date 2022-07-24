#!flask/bin/python
from operator import imod
from flask import Flask, jsonify, abort, make_response, request, url_for
import getcontainers
import getfirebase
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

# example
tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    }
]


CONTAINERS = getcontainers.HostController()
FIREBASE = getfirebase.Connect()
users = FIREBASE.get_users_base()

@app.route('/')
@auth.login_required
def index():
    return "Hey, %s!" % auth.current_user()


@app.route('/api/containers', methods=['GET'])
@auth.login_required
def get_containers():
    CONTAINERS.get_containers_info()
    return jsonify({'containers': list(map(make_public_container, CONTAINERS.containers))})

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': list(map(make_public_task, tasks))})

@app.route('/api/containers/<int:container_id>', methods=['GET'])
# @auth.login_required
def get_container(container_id):
    container = list(filter(lambda t: t["id"] == container_id, CONTAINERS.containers))
    if len(container) == 0:
        abort(404)
    return jsonify({'containers': container[0]})

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = list(filter(lambda c: c['id'] == task_id, tasks))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})

@auth.verify_password
def verify_password(username, password):
    userpass = FIREBASE.get_users_list()
    if username in userpass and \
            check_password_hash(userpass.get(username), password):
        return username

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task['id'], _scheme='https', _external=True)
        else:
            new_task[field] = task[field]
    return new_task

def make_public_container(container):
    new_container = {}
    for field in container:
        if field == 'id':
            new_container['uri'] = url_for('get_container', container_id=container['id'], _scheme='https',  _external=True)
        else:
            new_container[field] = container[field]
    return new_container

@app.route('/api/tasks', methods=['POST'])
@auth.login_required
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': tasks[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    tasks.append(task)
    return jsonify({'task': task}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@auth.login_required
def update_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, tasks))
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and not isinstance(request.json['title'], str):
        abort(400)
    if 'description' in request.json and not isinstance(request.json['description'], str):
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': task[0]})

# curl -i -H "Content-Type: application/json" -X PUT -d '{"version":v0.1.11}' http://localhost:5000/api/containers/1
# curl -u log:pass http://localhost:5000/api/containers | jq '.[] | .[] | select(."name"=="conta") | .uri'

@app.route('/api/containers/<int:container_id>', methods=['PUT'])
@auth.login_required
def update_container(container_id):
    container = list(filter(lambda t: t['id'] == container_id, CONTAINERS.containers))
    if len(container) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'description' in request.json and not isinstance(request.json['description'], str):
        abort(400)
    if 'image' in request.json and not isinstance(request.json['image'], str):
        abort(400)
    if 'version' in request.json and not isinstance(request.json['version'], str):
        abort(400)
    if 'commands' in request.json and not isinstance(request.json['commands'], str):
        abort(400)
    container[0]['description'] = request.json.get('description', container[0]['description'])
    container[0]['commands'] = request.json.get('commands', container[0]['commands'])
    container[0]['image'] = request.json.get('image', container[0]['image'])
    container[0]['version'] = request.json.get('version', container[0]['version'])
    if 'version' in request.json:
        print(CONTAINERS.upgrade_container(container[0]['name'], container[0]['version']))
    return jsonify({'container': container[0]})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@auth.login_required
def delete_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, tasks))
    if len(task) == 0:
        abort(404)
    tasks.remove(task[0])
    return jsonify({'result': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0')
