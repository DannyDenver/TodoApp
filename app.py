from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5444/dannydb'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
sys.dont_write_bytecode = True

class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=True)
    def __repr__(self):
        return '<Todo' + str(self.id) + ' ' + self.description + ' ' + str(self.completed) + '>'

class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=True)
    todos = db.relationship('Todo', cascade='all,delete-orphan', backref=db.backref('list', single_parent=True, cascade="all,delete-orphan"), lazy=True)

active_list = {}

@app.route('/lists/create', methods=['POST'])
def create_list():
    body = {}
    error = False
    try:
        description = request.get_json()['description']
        todo = TodoList(name=description)
        db.session.add(todo)
        db.session.commit()
        body['id'] = todo.id
        body['description'] = description
    except:
        db.session.rollback()
        error=True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    if not error:
        return jsonify(body)

@app.route('/lists/<list_id>/todos/create', methods=['POST'])
def create_todo(list_id):
    body = {}
    error = False
    try:
        print(list_id)
        description = request.get_json()['description']
        todo = Todo(description=description, completed=False, list_id=list_id)
        db.session.add(todo)
        db.session.commit()
        body['id'] = todo.id
        body['completed'] = todo.completed
        body['description'] = description
    except:
        db.session.rollback()
        error=True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    if not error:
        return jsonify(body)

@app.route('/lists/<list_id>/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed_todo(list_id, todo_id):
    try:
        completed = request.get_json()['completed']
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({ 'success': True })

@app.route('/lists/<list_id>/set-completed', methods=['POST'])
def set_completed_list(list_id):
    try:
        completed = request.get_json()['completed']
        list = TodoList.query.get(list_id)
        list.completed = completed
        todos = Todo.query.filter_by(list_id=list_id)
        todos.update({Todo.completed: completed })
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({ 'success': True })

@app.route('/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        db.session.query(Todo).filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({ 'success': True })

@app.route('/lists/<list_id>', methods=['DELETE'])
def delete_list(list_id):
    try:
        db.session.query(TodoList).filter_by(id=list_id).delete()
        db.session.commit()
    except:
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({ 'success': True })

@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    return render_template('index.html',
    lists=TodoList.query.order_by('id').all(),
    active_list=TodoList.query.get(list_id),
    todos=Todo.query.filter_by(list_id=list_id).order_by('id').all())

@app.route('/')
def index():
    firstId=db.session.query(TodoList).order_by('id').first().id
    return redirect(url_for('get_list_todos', list_id=firstId))
