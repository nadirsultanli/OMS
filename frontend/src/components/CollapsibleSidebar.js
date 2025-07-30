import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  UserPlus,
  Package, 
  DollarSign, 
  Warehouse,
  Menu,
  Pin,
  PinOff,
  Truck,
  ArrowLeftRight,
  X,
  Route,
  FileText,
  Archive,
  TrendingUp,
  Shield
} from 'lucide-react';
import { UserAvatar } from './ui/UserAvatar';
import authService from '../services/authService';
import './CollapsibleSidebar.css';

const CollapsibleSidebar = ({ onExpandChange }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isPinned, setIsPinned] = useState(() => {
    // Load pin state from localStorage
    const saved = localStorage.getItem('sidebarPinned');
    return saved === 'true';
  });
  const [isHovering, setIsHovering] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [showScrollbar, setShowScrollbar] = useState(false);
  const expandTimeout = useRef(null);
  const location = useLocation();
  const user = authService.getCurrentUser();

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/users', label: 'Users', icon: UserPlus },
    { path: '/customers', label: 'Customers', icon: Users },
    { path: '/orders', label: 'Orders', icon: FileText },
    { path: '/trips', label: 'Trips', icon: Route },
    { path: '/vehicles', label: 'Vehicles', icon: Truck },
    { path: '/products', label: 'Products', icon: Package },
    { path: '/variants', label: 'Variants', icon: Package },
    { path: '/price-lists', label: 'Price Lists', icon: DollarSign },
    { path: '/warehouses', label: 'Warehouses', icon: Warehouse },
    { path: '/stock', label: 'Stock Dashboard', icon: TrendingUp },
    { path: '/stock-levels', label: 'Stock Levels', icon: Archive },
    { path: '/stock-documents', label: 'Stock Documents', icon: ArrowLeftRight },
    { path: '/audit', label: 'Audit', icon: Shield },
    { path: '/mixed-load-capacity-test', label: 'Capacity Test', icon: TrendingUp }
  ];

  // Determine if sidebar should be expanded
  const shouldExpand = isPinned || isHovering;

  useEffect(() => {
    setIsExpanded(shouldExpand);
    onExpandChange?.(shouldExpand);
  }, [shouldExpand, onExpandChange]);

  // Show/hide scrollbar with animation delay
  useEffect(() => {
    if (isExpanded || isMobileOpen) {
      // Delay showing scrollbar until after expand animation (500ms)
      expandTimeout.current && clearTimeout(expandTimeout.current);
      expandTimeout.current = setTimeout(() => {
        setShowScrollbar(true);
      }, 500);
    } else {
      // Hide scrollbar immediately when collapsing
      expandTimeout.current && clearTimeout(expandTimeout.current);
      setShowScrollbar(false);
    }
    // Cleanup on unmount
    return () => {
      expandTimeout.current && clearTimeout(expandTimeout.current);
    };
  }, [isExpanded, isMobileOpen]);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileOpen(false);
  }, [location]);

  // Save pin state to localStorage
  useEffect(() => {
    localStorage.setItem('sidebarPinned', isPinned.toString());
  }, [isPinned]);

  const handleMouseEnter = () => {
    if (!isPinned) {
      setIsHovering(true);
    }
  };

  const handleMouseLeave = () => {
    if (!isPinned) {
      setIsHovering(false);
    }
  };

  const togglePin = () => {
    setIsPinned(!isPinned);
    if (!isPinned) {
      setIsHovering(false);
    }
  };

  const handleLogout = async () => {
    await authService.logout();
    window.location.href = '/login';
  };

  const isActive = (path) => {
    // Exact match for dashboard
    if (path === '/dashboard' && location.pathname === '/dashboard') return true;
    
    // Exact match for all other paths to avoid conflicts
    if (path !== '/dashboard' && location.pathname === path) return true;
    
    // For paths with sub-routes (like /customers/:id), check if it starts with the path
    // but exclude conflicting stock paths
    if (path !== '/dashboard' && path !== '/stock' && location.pathname.startsWith(path + '/')) return true;
    
    // Special handling for stock paths to avoid conflicts
    if (path === '/stock' && location.pathname === '/stock') return true;
    if (path === '/stock-levels' && location.pathname === '/stock-levels') return true;
    if (path === '/stock-documents' && location.pathname === '/stock-documents') return true;
    if (path === '/stock-dashboard' && location.pathname === '/stock-dashboard') return true;
    
    return false;
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileOpen(true)}
        className="mobile-menu-btn"
        aria-label="Open menu"
      >
        <Menu className="menu-icon" />
      </button>

      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="mobile-backdrop"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`sidebar ${isExpanded ? 'expanded' : 'collapsed'} ${isMobileOpen ? 'mobile-open' : ''}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {/* Mobile close button */}
        {isMobileOpen && (
          <div className="mobile-header">
            <button
              onClick={() => setIsMobileOpen(false)}
              className="mobile-close-btn"
              aria-label="Close menu"
            >
              <X className="close-icon" />
            </button>
          </div>
        )}

        {/* Navigation Menu */}
        <nav className={`nav-menu ${showScrollbar && (isExpanded || isMobileOpen) ? 'show-scrollbar' : ''}`}>
          <ul className="menu-list">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);

              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`menu-item ${active ? 'active' : ''}`}
                  >
                    <Icon className={`menu-icon ${active ? 'active-icon' : ''}`} />
                    
                    {/* Label - shown when expanded or on mobile */}
                    {(isExpanded || isMobileOpen) && (
                      <span className="menu-label">{item.label}</span>
                    )}

                    {/* Tooltip - shown when collapsed on desktop */}
                    {!isExpanded && !isMobileOpen && (
                      <div className="menu-tooltip">
                        {item.label}
                      </div>
                    )}

                    {/* Active indicator for collapsed state */}
                    {active && !isExpanded && !isMobileOpen && (
                      <div className="active-indicator" />
                    )}

                    {/* Badge if any */}
                    {item.badge && (
                      <span className={`menu-badge ${(isExpanded || isMobileOpen) ? 'expanded' : 'collapsed'}`}>
                        {item.badge}
                      </span>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom Section - Combined User and Logout */}
        <div className="bottom-section">
          {/* Pin/Unpin Button - only show when expanded */}
          {!isMobileOpen && (isExpanded || isPinned) && (
            <div className="pin-section">
              <button
                onClick={togglePin}
                className={`pin-btn ${isPinned ? 'pinned' : ''}`}
                title={isPinned ? 'Unpin Sidebar' : 'Keep Sidebar Open'}
              >
                {isPinned ? (
                  <PinOff className="pin-icon" />
                ) : (
                  <Pin className="pin-icon" />
                )}
                
                {/* Label - shown when expanded */}
                {isExpanded && (
                  <span className="pin-label">
                    {isPinned ? 'Unpin Sidebar' : 'Pin Sidebar'}
                  </span>
                )}
              </button>
            </div>
          )}

          {/* User and Logout Combined Section */}
          <div className="user-logout-section">
            {/* User Avatar - Always visible */}
            <div className="user-info">
              <UserAvatar 
                name={user?.name || user?.email || 'User'} 
                size="sm" 
                className="user-avatar"
              />

              {/* Tooltip - shown when collapsed on desktop */}
              {!isExpanded && !isMobileOpen && (
                <div className="user-tooltip">
                  {user?.name || user?.email}
                </div>
              )}
            </div>

            {/* Logout Button - only show when expanded */}
            {(isExpanded || isMobileOpen) && (
              <button
                onClick={handleLogout}
                className="logout-btn"
                title="Logout"
              >
                Logout
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default CollapsibleSidebar;