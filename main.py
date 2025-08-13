import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from src.models.user import db, User, Message, Group, GroupMember
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.messages import messages_bp
from src.routes.groups import groups_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(messages_bp, url_prefix='/api/messages')
app.register_blueprint(groups_bp, url_prefix='/api/groups')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        user_id = session['user_id']
        join_room(f'user_{user_id}')
        print(f'User {user_id} connected')
    else:
        print('Unauthorized connection attempt')

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        user_id = session['user_id']
        leave_room(f'user_{user_id}')
        print(f'User {user_id} disconnected')

@socketio.on('join_chat')
def handle_join_chat(data):
    if 'user_id' not in session:
        return
    
    chat_type = data.get('type')  # 'friend' or 'group'
    chat_id = data.get('id')
    
    if chat_type == 'friend':
        # Join private chat room
        room = f'private_{min(session["user_id"], chat_id)}_{max(session["user_id"], chat_id)}'
        join_room(room)
        print(f'User {session["user_id"]} joined private chat with {chat_id}')
    elif chat_type == 'group':
        # Check if user is member of the group
        member = GroupMember.query.filter_by(group_id=chat_id, user_id=session['user_id']).first()
        if member:
            room = f'group_{chat_id}'
            join_room(room)
            print(f'User {session["user_id"]} joined group {chat_id}')

@socketio.on('leave_chat')
def handle_leave_chat(data):
    if 'user_id' not in session:
        return
    
    chat_type = data.get('type')
    chat_id = data.get('id')
    
    if chat_type == 'friend':
        room = f'private_{min(session["user_id"], chat_id)}_{max(session["user_id"], chat_id)}'
        leave_room(room)
    elif chat_type == 'group':
        room = f'group_{chat_id}'
        leave_room(room)

@socketio.on('send_message')
def handle_send_message(data):
    if 'user_id' not in session:
        return
    
    chat_type = data.get('type')
    chat_id = data.get('id')
    content = data.get('content', '').strip()
    
    if not content:
        return
    
    try:
        if chat_type == 'friend':
            # Save message to database
            message = Message(
                sender_id=session['user_id'],
                receiver_id=chat_id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            
            # Get sender info
            sender = User.query.get(session['user_id'])
            
            # Emit to private chat room
            room = f'private_{min(session["user_id"], chat_id)}_{max(session["user_id"], chat_id)}'
            socketio.emit('new_message', {
                'id': message.id,
                'sender_id': message.sender_id,
                'sender_username': sender.username,
                'receiver_id': message.receiver_id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'type': 'friend'
            }, room=room)
            
            # Also emit to individual user rooms for notifications
            socketio.emit('message_notification', {
                'from_user': sender.username,
                'content': content,
                'type': 'friend'
            }, room=f'user_{chat_id}')
            
        elif chat_type == 'group':
            # Check if user is member of the group
            member = GroupMember.query.filter_by(group_id=chat_id, user_id=session['user_id']).first()
            if not member:
                return
            
            # Save message to database
            message = Message(
                sender_id=session['user_id'],
                group_id=chat_id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            
            # Get sender and group info
            sender = User.query.get(session['user_id'])
            group = Group.query.get(chat_id)
            
            # Emit to group room
            room = f'group_{chat_id}'
            socketio.emit('new_message', {
                'id': message.id,
                'sender_id': message.sender_id,
                'sender_username': sender.username,
                'group_id': message.group_id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'type': 'group'
            }, room=room)
            
            # Emit notifications to all group members
            members = GroupMember.query.filter_by(group_id=chat_id).all()
            for member in members:
                if member.user_id != session['user_id']:  # Don't notify sender
                    socketio.emit('message_notification', {
                        'from_user': sender.username,
                        'group_name': group.name,
                        'content': content,
                        'type': 'group'
                    }, room=f'user_{member.user_id}')
    
    except Exception as e:
        print(f'Error sending message: {e}')
        db.session.rollback()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
