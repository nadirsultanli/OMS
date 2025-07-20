import React from 'react';
import authService from '../services/authService';
import './Dashboard.css';

const Dashboard = () => {
  const user = authService.getCurrentUser();

  const handleLogout = async () => {
    await authService.logout();
    window.location.href = '/login';
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>LPG Order Management System</h1>
          <div className="user-info">
            <span>Welcome, {user?.name || user?.email}</span>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </header>
      
      <main className="dashboard-main">
        <div className="dashboard-content">
          <h2>Dashboard</h2>
          <p>You have successfully logged in to the LPG Order Management System.</p>
          
          <div className="user-details">
            <h3>User Information</h3>
            <p><strong>Email:</strong> {user?.email}</p>
            <p><strong>Role:</strong> {user?.role}</p>
            {user?.name && <p><strong>Name:</strong> {user.name}</p>}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;