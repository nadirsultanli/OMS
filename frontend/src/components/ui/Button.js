import React from 'react';
import './Button.css';

const Button = ({ 
    children, 
    color = 'primary', 
    size = 'medium', 
    className = '', 
    disabled = false,
    ...props 
}) => {
    return (
        <button 
            className={`btn btn-${color} btn-${size} ${className}`}
            disabled={disabled}
            {...props}
        >
            {children}
        </button>
    );
};

export default Button; 