from flask import Blueprint, jsonify, request, session
from src.models.user import User, Group, GroupMember, Message, db

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/create', methods=['POST'])
def create_group():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    data = request.json
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Tên nhóm không được để trống'}), 400
    
    try:
        # Tạo nhóm mới
        group = Group(name=name, creator_id=session['user_id'])
        db.session.add(group)
        db.session.flush()  # Để lấy ID của nhóm
        
        # Thêm người tạo vào nhóm
        member = GroupMember(group_id=group.id, user_id=session['user_id'])
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tạo nhóm thành công',
            'group': group.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@groups_bp.route('/add_member', methods=['POST'])
def add_member():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    data = request.json
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    
    if not group_id or not user_id:
        return jsonify({'success': False, 'error': 'ID nhóm và ID người dùng không được để trống'}), 400
    
    # Kiểm tra nhóm có tồn tại không
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'error': 'Nhóm không tồn tại'}), 404
    
    # Kiểm tra quyền (chỉ người tạo nhóm hoặc thành viên hiện tại mới có thể thêm người)
    current_member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if not current_member and group.creator_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Không có quyền thêm thành viên vào nhóm này'}), 403
    
    # Kiểm tra người dùng có tồn tại không
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Người dùng không tồn tại'}), 404
    
    # Kiểm tra xem người dùng đã là thành viên chưa
    existing_member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if existing_member:
        return jsonify({'success': False, 'error': 'Người dùng đã là thành viên của nhóm'}), 400
    
    try:
        # Thêm thành viên mới
        member = GroupMember(group_id=group_id, user_id=user_id)
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Thêm thành viên thành công'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@groups_bp.route('/remove_member', methods=['POST'])
def remove_member():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    data = request.json
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    
    if not group_id or not user_id:
        return jsonify({'success': False, 'error': 'ID nhóm và ID người dùng không được để trống'}), 400
    
    # Kiểm tra nhóm có tồn tại không
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'error': 'Nhóm không tồn tại'}), 404
    
    # Kiểm tra quyền (chỉ người tạo nhóm mới có thể xóa thành viên, hoặc thành viên tự rời nhóm)
    if group.creator_id != session['user_id'] and user_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Không có quyền xóa thành viên khỏi nhóm này'}), 403
    
    # Không cho phép xóa người tạo nhóm
    if user_id == group.creator_id:
        return jsonify({'success': False, 'error': 'Không thể xóa người tạo nhóm'}), 400
    
    # Tìm thành viên
    member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if not member:
        return jsonify({'success': False, 'error': 'Người dùng không phải là thành viên của nhóm'}), 404
    
    try:
        db.session.delete(member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Xóa thành viên thành công'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@groups_bp.route('/delete', methods=['POST'])
def delete_group():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    data = request.json
    group_id = data.get('group_id')
    
    if not group_id:
        return jsonify({'success': False, 'error': 'ID nhóm không được để trống'}), 400
    
    # Kiểm tra nhóm có tồn tại không
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'error': 'Nhóm không tồn tại'}), 404
    
    # Chỉ người tạo nhóm mới có thể xóa nhóm
    if group.creator_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Chỉ người tạo nhóm mới có thể xóa nhóm'}), 403
    
    try:
        # Xóa tất cả thành viên và tin nhắn (cascade delete)
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Xóa nhóm thành công'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@groups_bp.route('/send_message', methods=['POST'])
def send_group_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    data = request.json
    group_id = data.get('group_id')
    content = data.get('content', '').strip()
    
    if not group_id:
        return jsonify({'success': False, 'error': 'ID nhóm không được để trống'}), 400
    
    if not content:
        return jsonify({'success': False, 'error': 'Nội dung tin nhắn không được để trống'}), 400
    
    # Kiểm tra nhóm có tồn tại không
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'error': 'Nhóm không tồn tại'}), 404
    
    # Kiểm tra người dùng có phải là thành viên của nhóm không
    member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if not member:
        return jsonify({'success': False, 'error': 'Bạn không phải là thành viên của nhóm này'}), 403
    
    try:
        # Tạo tin nhắn nhóm
        message = Message(
            sender_id=session['user_id'],
            group_id=group_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Gửi tin nhắn nhóm thành công',
            'data': message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@groups_bp.route('/history', methods=['GET'])
def get_group_history():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    group_id = request.args.get('group_id')
    if not group_id:
        return jsonify({'success': False, 'error': 'ID nhóm không được để trống'}), 400
    
    try:
        group_id = int(group_id)
    except ValueError:
        return jsonify({'success': False, 'error': 'ID nhóm không hợp lệ'}), 400
    
    # Kiểm tra nhóm có tồn tại không
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'error': 'Nhóm không tồn tại'}), 404
    
    # Kiểm tra người dùng có phải là thành viên của nhóm không
    member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if not member:
        return jsonify({'success': False, 'error': 'Bạn không phải là thành viên của nhóm này'}), 403
    
    # Lấy lịch sử tin nhắn nhóm
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp.asc()).all()
    
    return jsonify({
        'success': True,
        'messages': [message.to_dict() for message in messages]
    }), 200

@groups_bp.route('/list', methods=['GET'])
def get_user_groups():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    # Lấy danh sách nhóm mà người dùng tham gia
    memberships = GroupMember.query.filter_by(user_id=session['user_id']).all()
    
    groups = []
    for membership in memberships:
        group = Group.query.get(membership.group_id)
        if group:
            group_data = group.to_dict()
            # Thêm thông tin số thành viên
            member_count = GroupMember.query.filter_by(group_id=group.id).count()
            group_data['member_count'] = member_count
            groups.append(group_data)
    
    return jsonify({
        'success': True,
        'groups': groups
    }), 200

@groups_bp.route('/<int:group_id>/members', methods=['GET'])
def get_group_members(group_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    # Kiểm tra nhóm có tồn tại không
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'error': 'Nhóm không tồn tại'}), 404
    
    # Kiểm tra người dùng có phải là thành viên của nhóm không
    member = GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first()
    if not member:
        return jsonify({'success': False, 'error': 'Bạn không phải là thành viên của nhóm này'}), 403
    
    # Lấy danh sách thành viên
    members = db.session.query(GroupMember, User).join(User).filter(GroupMember.group_id == group_id).all()
    
    member_list = []
    for membership, user in members:
        member_data = user.to_dict()
        member_data['joined_at'] = membership.joined_at.isoformat()
        member_data['is_creator'] = user.id == group.creator_id
        member_list.append(member_data)
    
    return jsonify({
        'success': True,
        'members': member_list
    }), 200

