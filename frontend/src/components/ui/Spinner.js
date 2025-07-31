import React from 'react';
import './Spinner.css';

const Spinner = ({ size = 'medium', className = '', ...props }) => {
    return (
        <div className={`spinner spinner-${size} ${className}`} {...props}>
            <div className="spinner-inner"></div>
        </div>
    );
};

export default Spinner; 