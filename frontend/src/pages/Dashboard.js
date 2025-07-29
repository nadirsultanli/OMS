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
import customerService from '../services/customerService';
import orderService from '../services/orderService';
import stockService from '../services/stockService';
import tripService from '../services/tripService';
import vehicleService from '../services/vehicleService';
import './Dashboard.css';

const Dashboard = () => {
  const user = authService.getCurrentUser();
  const [dashboardData, setDashboardData] = useState({
    customers: { total: 0, loading: true },
    orders: { total: 0, pending: 0, completed: 0, loading: true },
    stock: { lowStock: 0, totalProducts: 0, loading: true },
    trips: { active: 0, pending: 0, loading: true },
    vehicles: { total: 0, active: 0, loading: true }
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load customers count
      customerService.getCustomers({ limit: 1, offset: 0 })
        .then(response => {
          if (response.success) {
            setDashboardData(prev => ({
              ...prev,
              customers: { total: response.data.total || 0, loading: false }
            }));
          } else {
            setDashboardData(prev => ({
              ...prev,
              customers: { total: 0, loading: false }
            }));
          }
        })
        .catch(() => {
          setDashboardData(prev => ({
            ...prev,
            customers: { total: 0, loading: false }
          }));
        });

      // Load orders summary
      orderService.getOrders(null, { limit: 1000 })
        .then(response => {
          if (response.success) {
            const orders = response.data.orders || [];
            const pending = orders.filter(o => o.status === 'pending').length;
            const completed = orders.filter(o => o.status === 'completed').length;
            setDashboardData(prev => ({
              ...prev,
              orders: { total: orders.length, pending, completed, loading: false }
            }));
          } else {
            setDashboardData(prev => ({
              ...prev,
              orders: { total: 0, pending: 0, completed: 0, loading: false }
            }));
          }
        })
        .catch(() => {
          setDashboardData(prev => ({
            ...prev,
            orders: { total: 0, pending: 0, completed: 0, loading: false }
          }));
        });

      // Load stock levels
      stockService.getStockLevels({ limit: 1000 })
        .then(response => {
          const stockLevels = response.stock_levels || [];
          const lowStock = stockLevels.filter(s => s.current_quantity <= (s.minimum_quantity || 0)).length;
          setDashboardData(prev => ({
            ...prev,
            stock: { lowStock, totalProducts: stockLevels.length, loading: false }
          }));
        })
        .catch(() => {
          setDashboardData(prev => ({
            ...prev,
            stock: { lowStock: 0, totalProducts: 0, loading: false }
          }));
        });

      // Load trips summary
      tripService.getTrips({ limit: 1000 })
        .then(response => {
          if (response.success) {
            const trips = response.data.results || [];
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
        })
        .catch(() => {
          setDashboardData(prev => ({
            ...prev,
            trips: { active: 0, pending: 0, loading: false }
          }));
        });

      // Load vehicles summary
      const currentUser = authService.getCurrentUser();
      const tenantId = currentUser?.tenant_id;
      vehicleService.getVehicles(tenantId, { limit: 1000 })
        .then(response => {
          if (response.success) {
            const vehicles = response.data.results || [];
            const active = vehicles.filter(v => v.status === 'active').length;
            setDashboardData(prev => ({
              ...prev,
              vehicles: { total: vehicles.length, active, loading: false }
            }));
          } else {
            setDashboardData(prev => ({
              ...prev,
              vehicles: { total: 0, active: 0, loading: false }
            }));
          }
        })
        .catch(() => {
          setDashboardData(prev => ({
            ...prev,
            vehicles: { total: 0, active: 0, loading: false }
          }));
        });

    } catch (error) {
      console.error('Error loading dashboard data:', error);
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
          {loading ? '...' : value}
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
          <h2>Welcome back, {user?.name || user?.email}!</h2>
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
            {user?.name && (
              <div className="info-item">
                <strong>Name:</strong> {user.name}
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