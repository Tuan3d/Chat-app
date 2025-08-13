// WebSocket connection
let socket = null;

// Initialize WebSocket connection
function initializeSocket() {
    if (socket) {
        socket.disconnect();
    }
    
    socket = io();
    
    // Connection events
    socket.on('connect', () => {
        console.log('Connected to server');
        showNotification('Đã kết nối đến server', 'success');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        showNotification('Mất kết nối đến server', 'error');
    });
    
    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        showNotification('Lỗi kết nối', 'error');
    });
    
    // Message events
    socket.on('new_message', (data) => {
        handleNewMessage(data);
    });
    
    socket.on('message_notification', (data) => {
        handleMessageNotification(data);
    });
}

// Join a chat room
function joinChatRoom(chatData, type) {
    if (!socket) return;
    
    socket.emit('join_chat', {
        type: type,
        id: chatData.id
    });
}

// Leave a chat room
function leaveChatRoom(chatData, type) {
    if (!socket) return;
    
    socket.emit('leave_chat', {
        type: type,
        id: chatData.id
    });
}

// Send message via WebSocket
function sendMessageViaSocket(chatData, type, content) {
    if (!socket) return;
    
    socket.emit('send_message', {
        type: type,
        id: chatData.id,
        content: content
    });
}

// Handle incoming messages
function handleNewMessage(data) {
    // Only update if we're currently viewing this chat
    if (!currentChat || !currentChatType) return;
    
    const isCurrentChat = (
        (data.type === 'friend' && currentChatType === 'friend' && 
         (data.receiver_id === currentChat.id || data.sender_id === currentChat.id)) ||
        (data.type === 'group' && currentChatType === 'group' && data.group_id === currentChat.id)
    );
    
    if (isCurrentChat) {
        // Add message to current chat
        addMessageToChat(data);
    }
}

// Handle message notifications
function handleMessageNotification(data) {
    if (data.type === 'friend') {
        showNotification(`Tin nhắn mới từ ${data.from_user}: ${data.content}`, 'info');
    } else if (data.type === 'group') {
        showNotification(`Tin nhắn mới trong nhóm ${data.group_name} từ ${data.from_user}: ${data.content}`, 'info');
    }
}

// Add message to current chat display
function addMessageToChat(messageData) {
    const messagesArea = document.getElementById('messages-area');
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${messageData.sender_id === currentUser.id ? 'own' : ''}`;
    
    const messageTime = new Date(messageData.timestamp).toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    messageElement.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-user"></i>
        </div>
        <div class="message-content">
            <div class="message-text">${messageData.content}</div>
            <div class="message-time">${messageTime}</div>
        </div>
    `;
    
    messagesArea.appendChild(messageElement);
    
    // Scroll to bottom
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

// Disconnect WebSocket
function disconnectSocket() {
    if (socket) {
        socket.disconnect();
        socket = null;
    }
}

