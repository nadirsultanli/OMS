import React from 'react';
import authService from '../services/authService';
import './Dashboard.css';

const Dashboard = () => {
  const user = authService.getCurrentUser();

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="header-content">
          <div className="header-text">
            <h1 className="page-title">Dashboard</h1>
            <p className="page-subtitle">Welcome to LPG Order Management System</p>
          </div>
        </div>
      </div>
      
      <div className="dashboard-content">
        <div className="welcome-section">
          <h2>Welcome back, {user?.name || user?.email}!</h2>
          <p>You have successfully logged in to the LPG Order Management System.</p>
          
          <div className="user-details">
            <h3>Your Account Information</h3>
            <p><strong>Email:</strong> {user?.email}</p>
            <p><strong>Role:</strong> {user?.role}</p>
            {user?.name && <p><strong>Name:</strong> {user.name}</p>}
          </div>
          
          <div className="quick-actions">
            <h3>Quick Actions</h3>
            <p>Use the sidebar to navigate to different sections of the system.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;