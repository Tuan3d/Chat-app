# Chat App - Ứng dụng nhắn tin hoàn chỉnh

Ứng dụng web nhắn tin được xây dựng bằng Flask và WebSocket, hỗ trợ chat cá nhân, chat nhóm, kết bạn và nhiều tính năng khác.

## Tính năng chính

- ✅ Đăng ký tài khoản với ID tùy chỉnh (tối đa 16 ký tự)
- ✅ Đăng nhập/đăng xuất
- ✅ Tìm kiếm người dùng theo ID hoặc tên
- ✅ Gửi yêu cầu kết bạn và chấp nhận kết bạn
- ✅ Chat cá nhân realtime
- ✅ Tạo nhóm chat và quản lý thành viên
- ✅ Chat nhóm realtime
- ✅ Upload avatar
- ✅ Giao diện responsive (tự động căn chỉnh cho thiết bị)
- ✅ Chủ đề tối/sáng
- ✅ Database SQLite không mã hóa (theo yêu cầu)
- ✅ WebSocket cho tin nhắn realtime

## Cấu trúc dự án

```
chat-app/
├── src/
│   ├── main.py              # File chính của ứng dụng Flask
│   ├── models/
│   │   └── user.py          # Models database (User, Message, Group, etc.)
│   ├── routes/
│   │   ├── auth.py          # API đăng ký/đăng nhập
│   │   ├── user.py          # API quản lý người dùng và kết bạn
│   │   ├── messages.py      # API tin nhắn cá nhân
│   │   └── groups.py        # API nhóm chat
│   ├── static/              # Frontend files
│   │   ├── index.html       # Giao diện chính
│   │   ├── css/
│   │   │   ├── style.css    # CSS chính
│   │   │   └── dark-theme.css # CSS chủ đề tối
│   │   └── js/
│   │       ├── api.js       # Các hàm gọi API
│   │       ├── socket.js    # WebSocket client
│   │       └── app.js       # Logic chính của ứng dụng
│   └── database/
│       └── app.db           # Database SQLite
├── venv/                    # Virtual environment
├── requirements.txt         # Dependencies
└── README.md               # File hướng dẫn này
```

## Cài đặt và chạy

### 1. Cài đặt dependencies

```bash
cd chat-app
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Chạy ứng dụng

```bash
python src/main.py
```

Ứng dụng sẽ chạy tại: http://localhost:5000

### 3. Sử dụng với Serveo (Public access)

Để chia sẻ ứng dụng ra internet, mở terminal mới và chạy:

```bash
ssh -R 80:localhost:5000 serveo.net
```

## Hướng dẫn sử dụng

### 1. Đăng ký tài khoản
- Nhập tên đăng nhập, ID tùy chỉnh (tối đa 16 ký tự) và mật khẩu
- ID tùy chỉnh phải là duy nhất

### 2. Đăng nhập
- Có thể đăng nhập bằng tên đăng nhập hoặc ID tùy chỉnh

### 3. Tìm kiếm và kết bạn
- Vào tab "Tìm kiếm"
- Nhập tên hoặc ID của người dùng
- Nhấn "Kết bạn" để gửi yêu cầu

### 4. Chấp nhận kết bạn
- Vào tab "Bạn bè"
- Xem phần "Yêu cầu kết bạn"
- Nhấn ✓ để chấp nhận hoặc ✗ để từ chối

### 5. Chat cá nhân
- Nhấn vào tên bạn bè trong danh sách
- Nhập tin nhắn và nhấn Enter hoặc nút gửi

### 6. Tạo nhóm chat
- Vào tab "Nhóm"
- Nhấn nút "+" để tạo nhóm mới
- Nhập tên nhóm

### 7. Chat nhóm
- Nhấn vào tên nhóm trong danh sách
- Nhập tin nhắn và gửi

### 8. Thay đổi avatar
- Nhấn vào avatar của bạn ở góc trên bên trái
- Chọn file ảnh và tải lên

### 9. Chuyển đổi chủ đề
- Nhấn nút mặt trăng/mặt trời để chuyển đổi giữa chủ đề tối và sáng

## Cấu trúc Database

### Bảng User
- id: Primary key
- username: Tên đăng nhập (unique)
- password: Mật khẩu (không mã hóa)
- custom_id: ID tùy chỉnh (unique, tối đa 16 ký tự)
- avatar_url: Đường dẫn avatar

### Bảng Friendship
- user_id1, user_id2: ID của hai người dùng
- status: Trạng thái (pending, accepted, rejected)

### Bảng Message
- id: Primary key
- sender_id: ID người gửi
- receiver_id: ID người nhận (null nếu là tin nhắn nhóm)
- group_id: ID nhóm (null nếu là tin nhắn cá nhân)
- content: Nội dung tin nhắn
- timestamp: Thời gian gửi

### Bảng Group
- id: Primary key
- name: Tên nhóm
- creator_id: ID người tạo nhóm

### Bảng GroupMember
- group_id, user_id: ID nhóm và ID thành viên

## API Endpoints

### Auth
- POST /api/auth/register - Đăng ký
- POST /api/auth/login - Đăng nhập
- POST /api/auth/logout - Đăng xuất
- GET /api/auth/me - Lấy thông tin người dùng hiện tại
- POST /api/auth/upload_avatar - Tải avatar

### Users
- GET /api/users/search - Tìm kiếm người dùng
- POST /api/users/add_friend - Gửi yêu cầu kết bạn
- POST /api/users/accept_friend - Chấp nhận kết bạn
- GET /api/users/friends - Lấy danh sách bạn bè
- GET /api/users/friend_requests - Lấy yêu cầu kết bạn

### Messages
- POST /api/messages/send - Gửi tin nhắn cá nhân
- GET /api/messages/history - Lấy lịch sử tin nhắn
- GET /api/messages/conversations - Lấy danh sách cuộc trò chuyện

### Groups
- POST /api/groups/create - Tạo nhóm
- POST /api/groups/add_member - Thêm thành viên
- POST /api/groups/remove_member - Xóa thành viên
- POST /api/groups/delete - Xóa nhóm
- POST /api/groups/send_message - Gửi tin nhắn nhóm
- GET /api/groups/history - Lấy lịch sử tin nhắn nhóm
- GET /api/groups/list - Lấy danh sách nhóm
- GET /api/groups/{id}/members - Lấy danh sách thành viên

## WebSocket Events

### Client → Server
- connect - Kết nối
- join_chat - Tham gia phòng chat
- leave_chat - Rời phòng chat
- send_message - Gửi tin nhắn

### Server → Client
- new_message - Tin nhắn mới
- message_notification - Thông báo tin nhắn

## Lưu ý kỹ thuật

- Database SQLite không mã hóa mật khẩu (theo yêu cầu)
- WebSocket sử dụng Flask-SocketIO
- Frontend sử dụng vanilla JavaScript (không framework)
- Responsive design với CSS Media Queries
- CORS được bật cho phép frontend-backend interaction
- Session-based authentication

## Troubleshooting

### Lỗi kết nối database
- Đảm bảo thư mục `src/database/` tồn tại
- Database sẽ được tạo tự động khi chạy lần đầu

### Lỗi upload avatar
- Đảm bảo thư mục `src/static/uploads/` có quyền ghi
- Chỉ chấp nhận file ảnh: png, jpg, jpeg, gif

### Lỗi WebSocket
- Đảm bảo đã cài đặt flask-socketio
- Kiểm tra firewall không chặn port 5000

## Phát triển thêm

Để thêm tính năng mới:
1. Thêm model vào `src/models/user.py`
2. Tạo API endpoint trong `src/routes/`
3. Cập nhật frontend trong `src/static/`
4. Thêm WebSocket event nếu cần realtime

---

**Tác giả:** Manus AI Assistant  
**Ngày tạo:** 8/12/2025  
**Phiên bản:** 1.0

