import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Users, 
  Package, 
  FileText, 
  TrendingUp, 
  Route, 
  Truck,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign
} from 'lucide-react';
import authService from '../services/authService';
import api from '../services/api';
import customerService from '../services/customerService';
import orderService from '../services/orderService';
import stockService from '../services/stockService';
import tripService from '../services/tripService';
import vehicleService from '../services/vehicleService';
import './Dashboard.css';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [dashboardData, setDashboardData] = useState({
    customers: { total: 0, loading: true },
    orders: { total: 0, pending: 0, completed: 0, loading: true },
    stock: { lowStock: 0, totalProducts: 0, loading: true },
    trips: { active: 0, pending: 0, loading: true },
    vehicles: { total: 0, active: 0, loading: true }
  });

  // Fetch user data from API
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
      } catch (error) {
        console.error('Failed to fetch user data:', error);
        // Fallback to localStorage if API fails
        const fallbackUser = authService.getCurrentUser();
        setUser(fallbackUser);
      }
    };

    fetchUserData();
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const currentUser = authService.getCurrentUser();
      const tenantId = currentUser?.tenant_id;

      // Clear cache for debugging - remove this later
      const cacheKey = `dashboard_data_${tenantId}`;
      sessionStorage.removeItem(cacheKey);
      sessionStorage.removeItem(`${cacheKey}_time`);
      
      // Check for cached data first (cache for 30 seconds)
      // const cachedData = sessionStorage.getItem(cacheKey);
      // const cacheTime = sessionStorage.getItem(`${cacheKey}_time`);
      
      // if (cachedData && cacheTime && (Date.now() - parseInt(cacheTime)) < 30000) {
      //   try {
      //     const parsedData = JSON.parse(cachedData);
      //     setDashboardData(parsedData);
      //     return;
      //   } catch (e) {
      //     // Invalid cache, continue with fresh data
      //   }
      // }

      // Make all API calls in parallel for better performance
      // Use optimized summary endpoints for better performance
      const [
        customersResponse,
        ordersResponse,
        stockResponse,
        tripsResponse,
        vehiclesResponse,
        invoiceSummaryResponse,
        paymentSummaryResponse
      ] = await Promise.allSettled([
        // Load customers count - use smaller limit since we only need total
        customerService.getCustomers({ limit: 10, offset: 0 }),
        
        // Load orders summary - use optimized dashboard endpoint
        orderService.getOrdersSummary(tenantId),
        
        // Load stock levels - use smaller limit
        stockService.getStockLevels({ limit: 50 }),
        
        // Load trips summary - use smaller limit
        tripService.getTrips({ limit: 50 }),
        
        // Load vehicles summary - use optimized dashboard endpoint
        api.get(`/vehicles/summary/dashboard?tenant_id=${tenantId}`),
        
        // Load invoice summary (optimized endpoint)
        api.get('/invoices/summary/dashboard'),
        
        // Load payment summary (optimized endpoint)
        api.get('/payments/summary/dashboard')
      ]);

      // Process customers data
      if (customersResponse.status === 'fulfilled' && customersResponse.value.success) {
        setDashboardData(prev => ({
          ...prev,
          customers: { total: customersResponse.value.data.total || 0, loading: false }
        }));
      } else {
        setDashboardData(prev => ({
          ...prev,
          customers: { total: 0, loading: false }
        }));
      }

      // Process orders data (optimized endpoint)
      console.log('Orders API Response:', ordersResponse);
      if (ordersResponse.status === 'fulfilled' && ordersResponse.value.success) {
        const summary = ordersResponse.value.data.data;
        console.log('Orders Summary Data:', summary);
        setDashboardData(prev => ({
          ...prev,
          orders: { 
            total: summary.total || 0, 
            pending: summary.pending || 0, 
            completed: summary.completed || 0, 
            loading: false 
          }
        }));
      } else {
        console.error('Orders API Error:', ordersResponse);
        setDashboardData(prev => ({
          ...prev,
          orders: { total: 0, pending: 0, completed: 0, loading: false }
        }));
      }

      // Process stock data
      if (stockResponse.status === 'fulfilled') {
        const stockLevels = stockResponse.value.stock_levels || [];
        const lowStock = stockLevels.filter(s => s.current_quantity <= (s.minimum_quantity || 0)).length;
        setDashboardData(prev => ({
          ...prev,
          stock: { lowStock, totalProducts: stockLevels.length, loading: false }
        }));
      } else {
        setDashboardData(prev => ({
          ...prev,
          stock: { lowStock: 0, totalProducts: 0, loading: false }
        }));
      }

      // Process trips data
      if (tripsResponse.status === 'fulfilled' && tripsResponse.value.data.success) {
        const trips = tripsResponse.value.data.data.results || [];
        const active = trips.filter(t => t.status === 'IN_PROGRESS').length;
        const pending = trips.filter(t => t.status === 'PLANNED').length;
        setDashboardData(prev => ({
          ...prev,
          trips: { active, pending, loading: false }
        }));
      } else {
        setDashboardData(prev => ({
          ...prev,
          trips: { active: 0, pending: 0, loading: false }
        }));
      }

            // Process vehicles data (optimized endpoint)
      console.log('Vehicles API Response:', vehiclesResponse);
      if (vehiclesResponse.status === 'fulfilled' && vehiclesResponse.value.data.success) {
        const summary = vehiclesResponse.value.data.data;
        console.log('Vehicles Summary Data:', summary);
        setDashboardData(prev => ({
          ...prev,
          vehicles: { 
            total: summary.total || 0, 
            active: summary.active || 0, 
            loading: false 
          }
        }));
      } else {
        console.error('Vehicles API Error:', vehiclesResponse);
        setDashboardData(prev => ({
          ...prev,
          vehicles: { total: 0, active: 0, loading: false }
        }));
      }

      // Cache the final dashboard data
      const finalData = {
        customers: { total: 0, loading: false },
        orders: { total: 0, pending: 0, completed: 0, loading: false },
        stock: { lowStock: 0, totalProducts: 0, loading: false },
        trips: { active: 0, pending: 0, loading: false },
        vehicles: { total: 0, active: 0, loading: false }
      };

      // Update final data based on responses
      if (customersResponse.status === 'fulfilled' && customersResponse.value.success) {
        finalData.customers = { total: customersResponse.value.data.total || 0, loading: false };
      }
      if (ordersResponse.status === 'fulfilled' && ordersResponse.value.success) {
        const orders = ordersResponse.value.data.orders || [];
        const pending = orders.filter(o => o.status === 'pending').length;
        const completed = orders.filter(o => o.status === 'completed').length;
        finalData.orders = { total: orders.length, pending, completed, loading: false };
      }
      if (stockResponse.status === 'fulfilled') {
        const stockLevels = stockResponse.value.stock_levels || [];
        const lowStock = stockLevels.filter(s => s.current_quantity <= (s.minimum_quantity || 0)).length;
        finalData.stock = { lowStock, totalProducts: stockLevels.length, loading: false };
      }
      if (tripsResponse.status === 'fulfilled' && tripsResponse.value.success) {
        const trips = tripsResponse.value.data.results || [];
        const active = trips.filter(t => t.status === 'IN_PROGRESS').length;
        const pending = trips.filter(t => t.status === 'PLANNED').length;
        finalData.trips = { active, pending, loading: false };
      }
      if (vehiclesResponse.status === 'fulfilled' && vehiclesResponse.value.success) {
        const vehicles = vehiclesResponse.value.data.results || [];
        const active = vehicles.filter(v => v.status === 'active').length;
        finalData.vehicles = { total: vehicles.length, active, loading: false };
      }

      // Save to cache
      sessionStorage.setItem(cacheKey, JSON.stringify(finalData));
      sessionStorage.setItem(`${cacheKey}_time`, Date.now().toString());

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Set all loading states to false on error
      setDashboardData(prev => ({
        ...prev,
        customers: { ...prev.customers, loading: false },
        orders: { ...prev.orders, loading: false },
        stock: { ...prev.stock, loading: false },
        trips: { ...prev.trips, loading: false },
        vehicles: { ...prev.vehicles, loading: false }
      }));
    }
  };

  const MetricCard = ({ title, value, subtitle, icon: Icon, color, link, loading }) => (
    <div className="metric-card">
      <div className={`metric-icon ${color}`}>
        <Icon size={24} />
      </div>
      <div className="metric-content">
        <h3 className="metric-title">{title}</h3>
        <div className="metric-value">
          {loading ? (
            <div className="loading-skeleton">
              <div className="skeleton-bar"></div>
            </div>
          ) : (
            value
          )}
        </div>
        {subtitle && <p className="metric-subtitle">{subtitle}</p>}
        {link && (
          <Link to={link} className="metric-link">
            View Details →
          </Link>
        )}
      </div>
    </div>
  );

  const QuickActionCard = ({ title, description, icon: Icon, link, color }) => (
    <Link to={link} className="quick-action-card">
      <div className={`action-icon ${color}`}>
        <Icon size={20} />
      </div>
      <div className="action-content">
        <h4 className="action-title">{title}</h4>
        <p className="action-description">{description}</p>
      </div>
    </Link>
  );

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
          <h2>Welcome back, {user?.full_name || user?.email}!</h2>
          <p>Here's an overview of your LPG Order Management System.</p>
        </div>

        {/* Metrics Grid */}
        <div className="metrics-grid">
          <MetricCard
            title="Total Customers"
            value={dashboardData.customers.total}
            icon={Users}
            color="blue"
            link="/customers"
            loading={dashboardData.customers.loading}
          />
          
          <MetricCard
            title="Orders"
            value={dashboardData.orders.total}
            subtitle={`${dashboardData.orders.pending} pending, ${dashboardData.orders.completed} completed`}
            icon={FileText}
            color="green"
            link="/orders"
            loading={dashboardData.orders.loading}
          />
          
          <MetricCard
            title="Stock Alerts"
            value={dashboardData.stock.lowStock}
            subtitle={`${dashboardData.stock.totalProducts} total products`}
            icon={AlertTriangle}
            color="orange"
            link="/stock-levels"
            loading={dashboardData.stock.loading}
          />
          
          <MetricCard
            title="Active Trips"
            value={dashboardData.trips.active}
            subtitle={`${dashboardData.trips.pending} pending`}
            icon={Route}
            color="purple"
            link="/trips"
            loading={dashboardData.trips.loading}
          />
          
          <MetricCard
            title="Vehicles"
            value={dashboardData.vehicles.total}
            subtitle={`${dashboardData.vehicles.active} active vehicles`}
            icon={Truck}
            color="indigo"
            link="/vehicles"
            loading={dashboardData.vehicles.loading}
          />
        </div>

        {/* Quick Actions */}
        <div className="quick-actions-section">
          <h3>Quick Actions</h3>
          <div className="quick-actions-grid">
            <QuickActionCard
              title="Create Order"
              description="Create a new LPG order for customers"
              icon={FileText}
              link="/orders"
              color="blue"
            />
            
            <QuickActionCard
              title="Stock Dashboard"
              description="Monitor and manage inventory levels"
              icon={TrendingUp}
              link="/stock"
              color="green"
            />
            
            <QuickActionCard
              title="Plan Trip"
              description="Schedule delivery trips and routes"
              icon={Route}
              link="/trips"
              color="purple"
            />
            
            <QuickActionCard
              title="Manage Customers"
              description="View and manage customer accounts"
              icon={Users}
              link="/customers"
              color="orange"
            />
            
            <QuickActionCard
              title="Price Lists"
              description="Manage product pricing and lists"
              icon={DollarSign}
              link="/price-lists"
              color="indigo"
            />
            
            <QuickActionCard
              title="System Audit"
              description="View system activity and audit logs"
              icon={CheckCircle}
              link="/audit"
              color="gray"
            />
          </div>
        </div>

        {/* User Info */}
        <div className="user-info-section">
          <h3>Your Account Information</h3>
          <div className="user-info-grid">
            <div className="info-item">
              <strong>Email:</strong> {user?.email}
            </div>
            <div className="info-item">
              <strong>Role:</strong> {user?.role || 'User'}
            </div>
            {user?.full_name && (
              <div className="info-item">
                <strong>Name:</strong> {user.full_name}
              </div>
            )}
            <div className="info-item">
              <strong>Last Login:</strong> {new Date().toLocaleDateString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;