import React from 'react';

export const UserAvatar = ({ name, size = 'md', className = '' }) => {
  const initials = name
    ? name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  const sizeClasses = {
    sm: 'h-8 w-8 text-sm',
    md: 'h-10 w-10 text-base',
    lg: 'h-12 w-12 text-lg'
  };

  return (
    <div className={`
      ${sizeClasses[size]} 
      bg-gradient-to-br from-blue-500 to-blue-600 
      rounded-full flex items-center justify-center 
      text-white font-semibold shadow-lg
      ${className}
    `}>
      {initials}
    </div>
  );
};