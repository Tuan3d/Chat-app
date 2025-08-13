// Global Variables
let currentUser = null;
let currentChat = null;
let currentChatType = null; // 'friend' or 'group'
let friends = [];
let groups = [];
let messageRefreshInterval = null;

// DOM Elements
const loadingScreen = document.getElementById('loading-screen');
const authScreen = document.getElementById('auth-screen');
const chatApp = document.getElementById('chat-app');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const messageForm = document.getElementById('messageForm');
const avatarForm = document.getElementById('avatarForm');
const createGroupForm = document.getElementById('createGroupForm');

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Check if user is already logged in
        const response = await API.getCurrentUser();
        if (response.success) {
            currentUser = response.user;
            showChatApp();
        } else {
            showAuthScreen();
        }
    } catch (error) {
        showAuthScreen();
    } finally {
        hideLoadingScreen();
    }
});

// Loading Screen
function hideLoadingScreen() {
    loadingScreen.style.display = 'none';
}

// Auth Functions
function showAuthScreen() {
    authScreen.style.display = 'flex';
    chatApp.classList.add('hidden');
    disconnectSocket();
}

function showChatApp() {
    authScreen.style.display = 'none';
    chatApp.classList.remove('hidden');
    initializeChatApp();
    initializeSocket();
}

function showLogin() {
    document.getElementById('login-form').classList.add('active');
    document.getElementById('register-form').classList.remove('active');
}

function showRegister() {
    document.getElementById('login-form').classList.remove('active');
    document.getElementById('register-form').classList.add('active');
}

// Form Handlers
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();

    try {
        const response = await API.login(username, password);
        if (response.success) {
            currentUser = response.user;
            showNotification('Đăng nhập thành công!', 'success');
            showChatApp();
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
});

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('register-username').value.trim();
    const customId = document.getElementById('register-custom-id').value.trim();
    const password = document.getElementById('register-password').value.trim();

    try {
        const response = await API.register(username, customId, password);
        if (response.success) {
            showNotification('Đăng ký thành công! Vui lòng đăng nhập.', 'success');
            showLogin();
            // Clear form
            registerForm.reset();
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
});

messageForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const content = document.getElementById('message-input').value.trim();
    
    if (!content || !currentChat) return;

    try {
        // Send via WebSocket for real-time delivery
        sendMessageViaSocket(currentChat, currentChatType, content);
        
        document.getElementById('message-input').value = '';
    } catch (error) {
        showNotification(error.message, 'error');
    }
});

avatarForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = document.getElementById('avatar-file').files[0];
    
    if (!file) {
        showNotification('Vui lòng chọn file ảnh', 'error');
        return;
    }

    try {
        const response = await API.uploadAvatar(file);
        if (response.success) {
            showNotification('Tải avatar thành công!', 'success');
            document.getElementById('user-avatar').src = response.avatar_url;
            closeModal('avatar-modal');
            avatarForm.reset();
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
});

createGroupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('group-name').value.trim();
    
    if (!name) return;

    try {
        const response = await API.createGroup(name);
        if (response.success) {
            showNotification('Tạo nhóm thành công!', 'success');
            closeModal('create-group-modal');
            createGroupForm.reset();
            loadGroups();
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
});

// Chat App Initialization
async function initializeChatApp() {
    // Update user info
    document.getElementById('user-name').textContent = currentUser.username;
    document.getElementById('user-id').textContent = `@${currentUser.custom_id}`;
    
    if (currentUser.avatar_url) {
        document.getElementById('user-avatar').src = currentUser.avatar_url;
    }

    // Load initial data
    await loadFriends();
    await loadGroups();
    await loadFriendRequests();

    // Stop auto-refresh since we're using WebSocket now
    if (messageRefreshInterval) {
        clearInterval(messageRefreshInterval);
        messageRefreshInterval = null;
    }
}

// Tab Management
function showTab(tabName) {
    // Remove active class from all tabs and contents
    document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to selected tab and content
    document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Friends Management
async function loadFriends() {
    try {
        const response = await API.getFriends();
        if (response.success) {
            friends = response.friends;
            renderFriends();
        }
    } catch (error) {
        console.error('Error loading friends:', error);
    }
}

function renderFriends() {
    const friendsList = document.getElementById('friends-list');
    friendsList.innerHTML = '';

    friends.forEach(friend => {
        const friendElement = document.createElement('div');
        friendElement.className = 'friend-item';
        friendElement.onclick = () => openChat(friend, 'friend');
        
        friendElement.innerHTML = `
            <div class="friend-avatar">
                ${friend.avatar_url ? 
                    `<img src="${friend.avatar_url}" alt="${friend.username}">` : 
                    `<i class="fas fa-user"></i>`
                }
            </div>
            <div class="friend-info">
                <div class="friend-name">${friend.username}</div>
                <div class="friend-status">@${friend.custom_id}</div>
            </div>
        `;
        
        friendsList.appendChild(friendElement);
    });
}

async function loadFriendRequests() {
    try {
        const response = await API.getFriendRequests();
        if (response.success) {
            renderFriendRequests(response.requests);
        }
    } catch (error) {
        console.error('Error loading friend requests:', error);
    }
}

function renderFriendRequests(requests) {
    const requestsList = document.getElementById('friend-requests-list');
    requestsList.innerHTML = '';

    if (requests.length === 0) {
        requestsList.innerHTML = '<p style="color: #666; font-size: 14px;">Không có yêu cầu kết bạn nào</p>';
        return;
    }

    requests.forEach(request => {
        const requestElement = document.createElement('div');
        requestElement.className = 'friend-request';
        
        requestElement.innerHTML = `
            <div class="friend-request-info">
                <div class="friend-avatar">
                    ${request.user.avatar_url ? 
                        `<img src="${request.user.avatar_url}" alt="${request.user.username}">` : 
                        `<i class="fas fa-user"></i>`
                    }
                </div>
                <div>
                    <div style="font-weight: 500;">${request.user.username}</div>
                    <div style="font-size: 12px; color: #666;">@${request.user.custom_id}</div>
                </div>
            </div>
            <div class="friend-request-actions">
                <button class="btn btn-small btn-success" onclick="acceptFriendRequest(${request.user.id})">
                    <i class="fas fa-check"></i>
                </button>
                <button class="btn btn-small btn-danger" onclick="rejectFriendRequest(${request.user.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        requestsList.appendChild(requestElement);
    });
}

async function acceptFriendRequest(friendId) {
    try {
        const response = await API.acceptFriend(friendId);
        if (response.success) {
            showNotification('Đã chấp nhận kết bạn!', 'success');
            await loadFriends();
            await loadFriendRequests();
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function rejectFriendRequest(friendId) {
    // For now, just reload the requests (in a real app, you'd have a reject API)
    loadFriendRequests();
}

// Groups Management
async function loadGroups() {
    try {
        const response = await API.getUserGroups();
        if (response.success) {
            groups = response.groups;
            renderGroups();
        }
    } catch (error) {
        console.error('Error loading groups:', error);
    }
}

function renderGroups() {
    const groupsList = document.getElementById('groups-list');
    groupsList.innerHTML = '';

    groups.forEach(group => {
        const groupElement = document.createElement('div');
        groupElement.className = 'group-item';
        groupElement.onclick = () => openChat(group, 'group');
        
        groupElement.innerHTML = `
            <div class="group-avatar">
                <i class="fas fa-users"></i>
            </div>
            <div class="group-info">
                <div class="group-name">${group.name}</div>
                <div class="group-members">${group.member_count} thành viên</div>
            </div>
        `;
        
        groupsList.appendChild(groupElement);
    });
}

function showCreateGroupModal() {
    document.getElementById('create-group-modal').classList.add('active');
}

// Search Users
async function searchUsers() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;

    try {
        const response = await API.searchUsers(query);
        if (response.success) {
            renderSearchResults(response.users);
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function renderSearchResults(users) {
    const searchResults = document.getElementById('search-results');
    searchResults.innerHTML = '';

    if (users.length === 0) {
        searchResults.innerHTML = '<p style="color: #666;">Không tìm thấy người dùng nào</p>';
        return;
    }

    users.forEach(user => {
        const userElement = document.createElement('div');
        userElement.className = 'search-result';
        
        userElement.innerHTML = `
            <div class="search-result-info">
                <div class="friend-avatar">
                    ${user.avatar_url ? 
                        `<img src="${user.avatar_url}" alt="${user.username}">` : 
                        `<i class="fas fa-user"></i>`
                    }
                </div>
                <div>
                    <div style="font-weight: 500;">${user.username}</div>
                    <div style="font-size: 12px; color: #666;">@${user.custom_id}</div>
                </div>
            </div>
            <button class="btn btn-primary btn-small" onclick="sendFriendRequest(${user.id})">
                Kết bạn
            </button>
        `;
        
        searchResults.appendChild(userElement);
    });
}

async function sendFriendRequest(userId) {
    try {
        const response = await API.addFriend(userId);
        if (response.success) {
            showNotification('Đã gửi yêu cầu kết bạn!', 'success');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

// Chat Management
function openChat(chatData, type) {
    // Leave previous chat room
    if (currentChat && currentChatType) {
        leaveChatRoom(currentChat, currentChatType);
    }
    
    currentChat = chatData;
    currentChatType = type;
    
    // Join new chat room
    joinChatRoom(chatData, type);
    
    // Update active state
    document.querySelectorAll('.friend-item, .group-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // Show chat container
    document.getElementById('welcome-screen').style.display = 'none';
    document.getElementById('chat-container').classList.remove('hidden');
    
    // Update chat header
    document.getElementById('chat-name').textContent = chatData.username || chatData.name;
    
    if (type === 'friend') {
        document.getElementById('chat-status').textContent = 'Trực tuyến';
        if (chatData.avatar_url) {
            document.getElementById('chat-avatar').src = chatData.avatar_url;
        } else {
            document.getElementById('chat-avatar').src = 'https://via.placeholder.com/40';
        }
    } else {
        document.getElementById('chat-status').textContent = `${chatData.member_count} thành viên`;
        document.getElementById('chat-avatar').src = 'https://via.placeholder.com/40';
    }
    
    // Load messages
    loadMessages();
}

function closeChatContainer() {
    // Leave current chat room
    if (currentChat && currentChatType) {
        leaveChatRoom(currentChat, currentChatType);
    }
    
    document.getElementById('welcome-screen').style.display = 'flex';
    document.getElementById('chat-container').classList.add('hidden');
    currentChat = null;
    currentChatType = null;
    
    // Remove active state
    document.querySelectorAll('.friend-item, .group-item').forEach(item => {
        item.classList.remove('active');
    });
}

async function loadMessages() {
    if (!currentChat || !currentChatType) return;

    try {
        let response;
        if (currentChatType === 'friend') {
            response = await API.getMessageHistory(currentChat.id);
        } else {
            response = await API.getGroupHistory(currentChat.id);
        }
        
        if (response.success) {
            renderMessages(response.messages);
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

function renderMessages(messages) {
    const messagesArea = document.getElementById('messages-area');
    messagesArea.innerHTML = '';

    messages.forEach(message => {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender_id === currentUser.id ? 'own' : ''}`;
        
        const messageTime = new Date(message.timestamp).toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${message.content}</div>
                <div class="message-time">${messageTime}</div>
            </div>
        `;
        
        messagesArea.appendChild(messageElement);
    });
    
    // Scroll to bottom
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

// Theme Management
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    localStorage.setItem('darkTheme', isDark);
}

// Load theme preference
if (localStorage.getItem('darkTheme') === 'true') {
    document.body.classList.add('dark-theme');
}

// Modal Management
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Click outside modal to close
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Avatar click handler
document.getElementById('user-avatar').addEventListener('click', () => {
    document.getElementById('avatar-modal').classList.add('active');
});

// Logout
async function logout() {
    try {
        await API.logout();
        currentUser = null;
        currentChat = null;
        currentChatType = null;
        
        disconnectSocket();
        
        showNotification('Đã đăng xuất!', 'info');
        showAuthScreen();
        showLogin();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Search input enter key handler
document.getElementById('search-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchUsers();
    }
});

// Fullscreen on click
document.addEventListener('click', () => {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.warn(`Không thể bật fullscreen: ${err.message}`);
        });
    }
});

