from flask import Blueprint, jsonify, request, session
from src.models.user import User, Message, db
from sqlalchemy import or_, and_

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/send', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    data = request.json
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    
    if not receiver_id:
        return jsonify({'success': False, 'error': 'ID người nhận không được để trống'}), 400
    
    if not content:
        return jsonify({'success': False, 'error': 'Nội dung tin nhắn không được để trống'}), 400
    
    if receiver_id == session['user_id']:
        return jsonify({'success': False, 'error': 'Không thể gửi tin nhắn cho chính mình'}), 400
    
    # Kiểm tra xem người nhận có tồn tại không
    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'success': False, 'error': 'Người nhận không tồn tại'}), 404
    
    try:
        # Tạo tin nhắn mới
        message = Message(
            sender_id=session['user_id'],
            receiver_id=receiver_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Gửi tin nhắn thành công',
            'data': message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@messages_bp.route('/history', methods=['GET'])
def get_message_history():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    friend_id = request.args.get('friend_id')
    if not friend_id:
        return jsonify({'success': False, 'error': 'ID bạn bè không được để trống'}), 400
    
    try:
        friend_id = int(friend_id)
    except ValueError:
        return jsonify({'success': False, 'error': 'ID bạn bè không hợp lệ'}), 400
    
    # Lấy lịch sử tin nhắn giữa hai người
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == session['user_id'], Message.receiver_id == friend_id),
            and_(Message.sender_id == friend_id, Message.receiver_id == session['user_id'])
        )
    ).order_by(Message.timestamp.asc()).all()
    
    return jsonify({
        'success': True,
        'messages': [message.to_dict() for message in messages]
    }), 200

@messages_bp.route('/conversations', methods=['GET'])
def get_conversations():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    # Lấy danh sách cuộc trò chuyện (tin nhắn gần nhất với mỗi người)
    subquery = db.session.query(
        Message.id,
        Message.sender_id,
        Message.receiver_id,
        Message.content,
        Message.timestamp,
        db.func.row_number().over(
            partition_by=db.case(
                (Message.sender_id == session['user_id'], Message.receiver_id),
                else_=Message.sender_id
            ),
            order_by=Message.timestamp.desc()
        ).label('rn')
    ).filter(
        or_(Message.sender_id == session['user_id'], Message.receiver_id == session['user_id'])
    ).subquery()
    
    latest_messages = db.session.query(subquery).filter(subquery.c.rn == 1).all()
    
    conversations = []
    for msg in latest_messages:
        # Xác định ID của người bạn
        friend_id = msg.receiver_id if msg.sender_id == session['user_id'] else msg.sender_id
        friend = User.query.get(friend_id)
        
        if friend:
            conversations.append({
                'friend': friend.to_dict(),
                'last_message': {
                    'id': msg.id,
                    'sender_id': msg.sender_id,
                    'receiver_id': msg.receiver_id,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat()
                }
            })
    
    # Sắp xếp theo thời gian tin nhắn gần nhất
    conversations.sort(key=lambda x: x['last_message']['timestamp'], reverse=True)
    
    return jsonify({
        'success': True,
        'conversations': conversations
    }), 200

