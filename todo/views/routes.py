from flask import Blueprint, jsonify
from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta
 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})

@api.route('/todos', methods=['GET'])
def get_todos():
    query = Todo.query

    # List of attributes that are allowed to filter
    filterable_fields = ['id', 'title', 'description', 'completed', 'deadline_at', 'created_at', 'updated_at']

    for field in filterable_fields:
        value = request.args.get(field)
        if value is not None:
            # Handle special cases for data types
            column_attr = getattr(Todo, field)

            if field == 'completed':
                value = value.lower() == 'true'
                query = query.filter(column_attr == value)
            elif field in ['id']:
                query = query.filter(column_attr == int(value))
            else:
                query = query.filter(column_attr == value)

    # Handle the window parameter
    window = request.args.get('window')
    if window is not None:
        try:
            days = int(window)
            end_date = datetime.utcnow() + timedelta(days=days)
            query = query.filter(Todo.deadline_at <= end_date)
        except ValueError:
            return jsonify({'error': 'Invalid window value'}), 400
    
    todos = query.all()
    result = [todo.to_dict() for todo in todos]
    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo(): 
    data = request.get_json()
    
    # Basic required field check
    if not data or 'title' not in data:
        return jsonify({'error': 'Missing required field: title'}), 400

    # Validate 'completed' field if provided
    completed = data.get('completed', False)
    if isinstance(completed, str):
        if completed.lower() in ['true', 'false']:
            completed = completed.lower() == 'true'
        else:
            return jsonify({'error': 'Invalid value for completed. Must be true or false.'}), 400
    elif not isinstance(completed, bool):
        completed = False  # default if weird type comes through

    # Validate 'deadline_at' if provided
    deadline_at = None
    if 'deadline_at' in data:
        try:
            deadline_at = datetime.fromisoformat(data['deadline_at'])
        except ValueError:
            return jsonify({'error': 'Invalid date format for deadline_at. Use ISO 8601 format.'}), 400

    fields = ['id', 'title', 'description', 'completed', 'deadline_at', 'created_at', 'updated_at']
    extra_fields = [key for key in data.keys() if key not in fields]
    if extra_fields:
        return jsonify({'error': 'Unexpected fields'}), 400
    
    # Create the todo
    todo = Todo(
        title=data['title'],
        description=data.get('description', ''),
        completed=completed,
        deadline_at=deadline_at
    )

    # Save to DB
    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)

    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    if todo.id != request.json.get('id', todo.id):
        return jsonify({'error': 'Invalid todo ID'}), 400
    
    fields = ['id', 'title', 'description', 'completed', 'deadline_at', 'created_at', 'updated_at']
    data = request.get_json()
    extra_fields = [key for key in data.keys() if key not in fields]
    if extra_fields:
        return jsonify({'error': 'Unexpected fields'}), 400
    
    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    db.session.commit()
    return jsonify(todo.to_dict())

@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200
    
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
 
