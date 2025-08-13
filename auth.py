from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
import os
from werkzeug.utils import secure_filename

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        custom_id = data.get('custom_id', '').strip()
        
        # Kiểm tra dữ liệu đầu vào
        if not username or not password or not custom_id:
            return jsonify({'success': False, 'error': 'Tên người dùng, mật khẩu và ID tùy chỉnh không được để trống'}), 400
        
        if len(custom_id) > 16:
            return jsonify({'success': False, 'error': 'ID tùy chỉnh không được vượt quá 16 ký tự'}), 400
        
        # Kiểm tra xem username hoặc custom_id đã tồn tại chưa
        existing_user = User.query.filter((User.username == username) | (User.custom_id == custom_id)).first()
        if existing_user:
            if existing_user.username == username:
                return jsonify({'success': False, 'error': 'Tên người dùng đã tồn tại'}), 400
            else:
                return jsonify({'success': False, 'error': 'ID tùy chỉnh đã tồn tại'}), 400
        
        # Tạo người dùng mới (mật khẩu không mã hóa theo yêu cầu)
        new_user = User(username=username, password=password, custom_id=custom_id)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Đăng ký thành công',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Tên người dùng và mật khẩu không được để trống'}), 400
        
        # Tìm người dùng theo username hoặc custom_id
        user = User.query.filter((User.username == username) | (User.custom_id == username)).first()
        
        if not user or user.password != password:  # So sánh mật khẩu không mã hóa
            return jsonify({'success': False, 'error': 'Tên người dùng hoặc mật khẩu không đúng'}), 401
        
        # Lưu thông tin người dùng vào session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'success': True,
            'message': 'Đăng nhập thành công',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Đăng xuất thành công'}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'success': False, 'error': 'Người dùng không tồn tại'}), 404
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Chưa đăng nhập'}), 401
    
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file được tải lên'}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Không có file được chọn'}), 400
    
    # Kiểm tra định dạng file
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Chỉ chấp nhận file ảnh (png, jpg, jpeg, gif)'}), 400
    
    try:
        # Tạo thư mục uploads nếu chưa tồn tại
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Lưu file với tên an toàn
        filename = secure_filename(f"avatar_{session['user_id']}_{file.filename}")
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Cập nhật URL avatar trong database
        user = User.query.get(session['user_id'])
        user.avatar_url = f'/uploads/{filename}'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tải avatar thành công',
            'avatar_url': user.avatar_url
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

