from flask import Blueprint, jsonify, request, session
from src.models.user import User, Friendship, db
from sqlalchemy import or_, and_

user_bp = Blueprint('user', __name__)

@user_bp.route('/search', methods=['GET'])
def search_users():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'Từ khóa tìm kiếm không được để trống'}), 400
    
    # Tìm kiếm theo custom_id hoặc username
    users = User.query.filter(
        or_(User.custom_id.ilike(f'%{query}%'), User.username.ilike(f'%{query}%'))
    ).filter(User.id != session['user_id']).limit(20).all()
    
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in users]
    }), 200

@user_bp.route('/add_friend', methods=['POST'])
def add_friend():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    data = request.json
    friend_id = data.get('friend_id')
    
    if not friend_id:
        return jsonify({'success': False, 'error': 'ID bạn bè không được để trống'}), 400
    
    if friend_id == session['user_id']:
        return jsonify({'success': False, 'error': 'Không thể kết bạn với chính mình'}), 400
    
    # Kiểm tra xem người dùng có tồn tại không
    friend = User.query.get(friend_id)
    if not friend:
        return jsonify({'success': False, 'error': 'Người dùng không tồn tại'}), 404
    
    # Kiểm tra xem đã có mối quan hệ bạn bè chưa
    existing_friendship = Friendship.query.filter(
        or_(
            and_(Friendship.user_id1 == session['user_id'], Friendship.user_id2 == friend_id),
            and_(Friendship.user_id1 == friend_id, Friendship.user_id2 == session['user_id'])
        )
    ).first()
    
    if existing_friendship:
        if existing_friendship.status == 'accepted':
            return jsonify({'success': False, 'error': 'Đã là bạn bè'}), 400
        elif existing_friendship.status == 'pending':
            return jsonify({'success': False, 'error': 'Yêu cầu kết bạn đang chờ xử lý'}), 400
    
    try:
        # Tạo yêu cầu kết bạn mới
        friendship = Friendship(user_id1=session['user_id'], user_id2=friend_id, status='pending')
        db.session.add(friendship)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Gửi yêu cầu kết bạn thành công'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/accept_friend', methods=['POST'])
def accept_friend():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    data = request.json
    friend_id = data.get('friend_id')
    
    if not friend_id:
        return jsonify({'success': False, 'error': 'ID bạn bè không được để trống'}), 400
    
    # Tìm yêu cầu kết bạn
    friendship = Friendship.query.filter(
        Friendship.user_id1 == friend_id,
        Friendship.user_id2 == session['user_id'],
        Friendship.status == 'pending'
    ).first()
    
    if not friendship:
        return jsonify({'success': False, 'error': 'Không tìm thấy yêu cầu kết bạn'}), 404
    
    try:
        friendship.status = 'accepted'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chấp nhận kết bạn thành công'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/friends', methods=['GET'])
def get_friends():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    # Lấy danh sách bạn bè đã chấp nhận
    friendships = db.session.query(Friendship).filter(
        or_(
            and_(Friendship.user_id1 == session['user_id'], Friendship.status == 'accepted'),
            and_(Friendship.user_id2 == session['user_id'], Friendship.status == 'accepted')
        )
    ).all()
    
    friends = []
    for friendship in friendships:
        friend_id = friendship.user_id2 if friendship.user_id1 == session['user_id'] else friendship.user_id1
        friend = User.query.get(friend_id)
        if friend:
            friends.append(friend.to_dict())
    
    return jsonify({
        'success': True,
        'friends': friends
    }), 200

@user_bp.route('/friend_requests', methods=['GET'])
def get_friend_requests():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    # Lấy danh sách yêu cầu kết bạn đang chờ
    pending_requests = Friendship.query.filter(
        Friendship.user_id2 == session['user_id'],
        Friendship.status == 'pending'
    ).all()
    
    requests = []
    for request in pending_requests:
        user = User.query.get(request.user_id1)
        if user:
            requests.append({
                'user': user.to_dict(),
                'created_at': request.created_at.isoformat()
            })
    
    return jsonify({
        'success': True,
        'requests': requests
    }), 200
