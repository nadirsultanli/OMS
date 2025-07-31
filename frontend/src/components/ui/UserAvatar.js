import React from 'react';
import './UserAvatar.css';

export const UserAvatar = ({ user, size = 'medium', className = '' }) => {
  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getAvatarColor = (name) => {
    if (!name) return '#6b7280';
    
    const colors = [
      '#3b82f6', '#ef4444', '#10b981', '#f59e0b', 
      '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
    ];
    
    const hash = name.split('').reduce((acc, char) => {
      return char.charCodeAt(0) + ((acc << 5) - acc);
    }, 0);
    
    return colors[Math.abs(hash) % colors.length];
  };

  const displayName = user?.name || user?.email || 'User';
  const initials = getInitials(displayName);
  const backgroundColor = getAvatarColor(displayName);

  return (
    <div 
      className={`user-avatar user-avatar-${size} ${className}`}
      style={{ backgroundColor }}
      title={displayName}
    >
      {initials}
    </div>
  );
};