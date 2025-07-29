import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Verification from './pages/Verification';
import PasswordReset from './pages/PasswordReset';
import AcceptInvitation from './pages/AcceptInvitation';
import AuthCallback from './pages/AuthCallback';
import Users from './pages/Users';
import Customers from './pages/Customers';
import CustomerDetail from './pages/CustomerDetail';
import Warehouses from './pages/Warehouses';
import WarehouseDetail from './pages/WarehouseDetail';
import Products from './pages/Products';
import PriceLists from './pages/PriceLists';
import PriceListDetail from './pages/PriceListDetail';
import Variants from './pages/Variants';
import Orders from './pages/Orders';
import OrderDetailView from './pages/OrderDetailView';
import StockDashboard from './pages/StockDashboard';
import StockLevels from './pages/StockLevels';
import StockDocuments from './pages/StockDocuments';
import Trips from './pages/Trips';
import Vehicles from './pages/Vehicles';
import Audit from './pages/Audit';
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
              path="/orders"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Orders />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/orders/:orderId"
              element={
                <ProtectedRoute>
                  <Layout>
                    <OrderDetailView />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/stock"
              element={
                <ProtectedRoute>
                  <Layout>
                    <StockDashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/stock-dashboard"
              element={
                <ProtectedRoute>
                  <Layout>
                    <StockDashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/stock-levels"
              element={
                <ProtectedRoute>
                  <Layout>
                    <StockLevels />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/stock-documents"
              element={
                <ProtectedRoute>
                  <Layout>
                    <StockDocuments />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/trips"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Trips />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/vehicles"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Vehicles />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/audit"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Audit />
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
          
          {/* Auth callback route - handles Supabase redirects */}
          <Route 
            path="/auth/callback" 
            element={<AuthCallback />} 
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