import React from 'react';
import './Alert.css';

const Alert = ({ children, type = 'info', className = '', ...props }) => {
    return (
        <div className={`alert alert-${type} ${className}`} {...props}>
            {children}
        </div>
    );
};

export default Alert; 