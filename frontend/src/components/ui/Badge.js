import React from 'react';
import './Badge.css';

const Badge = ({ children, color = 'primary', className = '', ...props }) => {
    return (
        <span className={`badge badge-${color} ${className}`} {...props}>
            {children}
        </span>
    );
};

export default Badge; 