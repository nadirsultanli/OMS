import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Verification from './pages/Verification';
import PasswordReset from './pages/PasswordReset';
import AcceptInvitation from './pages/AcceptInvitation';
import Users from './pages/Users';
import Customers from './pages/Customers';
import CustomerDetail from './pages/CustomerDetail';
import Warehouses from './pages/Warehouses';
import WarehouseDetail from './pages/WarehouseDetail';
import Products from './pages/Products';
import PriceLists from './pages/PriceLists';
import PriceListDetail from './pages/PriceListDetail';
import Variants from './pages/Variants';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import authService from './services/authService';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Public routes */}
          <Route 
            path="/login" 
            element={
              authService.isAuthenticated() ? 
              <Navigate to="/dashboard" replace /> : 
              <Login />
            } 
          />
          
          {/* Verification routes */}
          <Route 
            path="/verify" 
            element={<Verification />} 
          />
          <Route 
            path="/verify-email" 
            element={<Verification />} 
          />
          
          {/* Password reset route */}
          <Route 
            path="/reset-password" 
            element={<PasswordReset />} 
          />
          
          {/* Accept invitation route */}
          <Route 
            path="/accept-invitation" 
            element={<AcceptInvitation />} 
          />
          <Route 
            path="/invite" 
            element={<AcceptInvitation />} 
          />
          
          {/* Protected routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/users" 
            element={
              <ProtectedRoute>
                <Layout>
                  <Users />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/customers" 
            element={
              <ProtectedRoute>
                <Layout>
                  <Customers />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/customers/:customerId" 
            element={
              <ProtectedRoute>
                <Layout>
                  <CustomerDetail />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/warehouses" 
            element={
              <ProtectedRoute>
                <Layout>
                  <Warehouses />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/warehouses/:warehouseId" 
            element={
              <ProtectedRoute>
                <Layout>
                  <WarehouseDetail />
                </Layout>
              </ProtectedRoute>
            } 
          />
                      <Route
              path="/products"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Products />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/variants"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Variants />
                  </Layout>
                </ProtectedRoute>
              }
            />
          <Route 
            path="/price-lists" 
            element={
              <ProtectedRoute>
                <Layout>
                  <PriceLists />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/price-lists/:priceListId" 
            element={
              <ProtectedRoute>
                <Layout>
                  <PriceListDetail />
                </Layout>
              </ProtectedRoute>
            } 
          />
          
          {/* Default redirect */}
          <Route 
            path="/" 
            element={
              <Navigate to={authService.isAuthenticated() ? "/dashboard" : "/login"} replace />
            } 
          />
          
          {/* Catch all route */}
          <Route 
            path="*" 
            element={
              <Navigate to={authService.isAuthenticated() ? "/dashboard" : "/login"} replace />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;