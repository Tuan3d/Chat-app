// API Base URL
const API_BASE = '/api';

// API Helper Functions
class API {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth APIs
    static async register(username, customId, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                username,
                custom_id: customId,
                password
            })
        });
    }

    static async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                username,
                password
            })
        });
    }

    static async logout() {
        return this.request('/auth/logout', {
            method: 'POST'
        });
    }

    static async getCurrentUser() {
        return this.request('/auth/me');
    }

    static async uploadAvatar(file) {
        const formData = new FormData();
        formData.append('avatar', file);
        
        const response = await fetch(`${API_BASE}/auth/upload_avatar`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }
        
        return data;
    }

    // User APIs
    static async searchUsers(query) {
        return this.request(`/users/search?q=${encodeURIComponent(query)}`);
    }

    static async addFriend(friendId) {
        return this.request('/users/add_friend', {
            method: 'POST',
            body: JSON.stringify({
                friend_id: friendId
            })
        });
    }

    static async acceptFriend(friendId) {
        return this.request('/users/accept_friend', {
            method: 'POST',
            body: JSON.stringify({
                friend_id: friendId
            })
        });
    }

    static async getFriends() {
        return this.request('/users/friends');
    }

    static async getFriendRequests() {
        return this.request('/users/friend_requests');
    }

    // Message APIs
    static async sendMessage(receiverId, content) {
        return this.request('/messages/send', {
            method: 'POST',
            body: JSON.stringify({
                receiver_id: receiverId,
                content
            })
        });
    }

    static async getMessageHistory(friendId) {
        return this.request(`/messages/history?friend_id=${friendId}`);
    }

    static async getConversations() {
        return this.request('/messages/conversations');
    }

    // Group APIs
    static async createGroup(name) {
        return this.request('/groups/create', {
            method: 'POST',
            body: JSON.stringify({
                name
            })
        });
    }

    static async addGroupMember(groupId, userId) {
        return this.request('/groups/add_member', {
            method: 'POST',
            body: JSON.stringify({
                group_id: groupId,
                user_id: userId
            })
        });
    }

    static async removeGroupMember(groupId, userId) {
        return this.request('/groups/remove_member', {
            method: 'POST',
            body: JSON.stringify({
                group_id: groupId,
                user_id: userId
            })
        });
    }

    static async deleteGroup(groupId) {
        return this.request('/groups/delete', {
            method: 'POST',
            body: JSON.stringify({
                group_id: groupId
            })
        });
    }

    static async sendGroupMessage(groupId, content) {
        return this.request('/groups/send_message', {
            method: 'POST',
            body: JSON.stringify({
                group_id: groupId,
                content
            })
        });
    }

    static async getGroupHistory(groupId) {
        return this.request(`/groups/history?group_id=${groupId}`);
    }

    static async getUserGroups() {
        return this.request('/groups/list');
    }

    static async getGroupMembers(groupId) {
        return this.request(`/groups/${groupId}/members`);
    }
}

