import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, Badge, Alert, Spinner } from '../components/ui';
import { apiService } from '../services/apiService';
import subscriptionService from '../services/subscriptionService';
import './Subscriptions.css';

const Subscriptions = () => {
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedPlan, setSelectedPlan] = useState(null);
    const [subscription, setSubscription] = useState(null);
    const [usage, setUsage] = useState(null);

    const fetchPlans = async () => {
        try {
            setLoading(true);
            const response = await apiService.get('/subscriptions/plans');
            setPlans(response.plans || []);
        } catch (err) {
            setError('Failed to load subscription plans');
            console.error('Error fetching plans:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchUsage = useCallback(async (tenantId) => {
        try {
            const response = await apiService.get(`/subscriptions/usage/${tenantId}`);
            setUsage(response);
        } catch (err) {
            console.error('Error fetching usage:', err);
        }
    }, []);

    const fetchCurrentSubscription = useCallback(async () => {
        try {
            const response = await apiService.get('/subscriptions/current');
            setSubscription(response);
            fetchUsage(response.tenant_id);
        } catch (err) {
            if (err.response?.status === 404) {
                // No subscription found, that's okay
                setSubscription(null);
            } else {
                console.error('Error fetching current subscription:', err);
            }
        }
    }, [fetchUsage]);

    const handlePlanSelect = (plan) => {
        setSelectedPlan(plan);
    };

    const handleSubscribe = async () => {
        if (!selectedPlan) return;

        try {
            setLoading(true);
            
            // If user has existing subscription, use upgrade endpoint
            const endpoint = subscription ? '/subscriptions/upgrade' : '/subscriptions';
            const requestData = subscription 
                ? {
                    plan_id: selectedPlan.id,
                    billing_cycle: 'monthly'
                }
                : {
                    plan_id: selectedPlan.id,
                    billing_cycle: 'monthly',
                    trial_days: 14
                };
            
            const response = await apiService.post(endpoint, requestData);
            
            // If we have a payment URL, redirect to Stripe
            if (response.payment_url) {
                window.location.href = response.payment_url;
                return;
            }
            
            // Update local state
            setSubscription(response.subscription);
            setSelectedPlan(null);
            fetchCurrentSubscription();
            
            // Show success message
            const message = subscription 
                ? 'Subscription upgraded successfully! Your plan will be updated immediately.'
                : 'Subscription created successfully! You can now use the platform.';
            alert(message);
        } catch (err) {
            if (err.response?.status === 400 && err.response?.data?.detail?.includes('already has an active subscription')) {
                setError('You already have an active subscription. Please use the upgrade option above.');
            } else if (err.response?.status === 401) {
                setError('Your session has expired. Please refresh the page and try again.');
            } else {
                setError('Failed to process subscription. Please try again.');
            }
            console.error('Error processing subscription:', err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'active': return 'success';
            case 'trial': return 'warning';
            case 'past_due': return 'danger';
            case 'suspended': return 'danger';
            case 'cancelled': return 'secondary';
            default: return 'secondary';
        }
    };

    useEffect(() => {
        fetchPlans();
        fetchCurrentSubscription();
    }, [fetchCurrentSubscription]);



    const getUsageColor = (percentage) => {
        if (percentage >= 90) return 'danger';
        if (percentage >= 75) return 'warning';
        return 'success';
    };

    if (loading && plans.length === 0) {
        return (
            <div className="subscriptions-container">
                <div className="loading-container">
                    <Spinner size="large" />
                    <p>Loading subscription plans...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="subscriptions-container">
            <div className="subscriptions-header">
                <h1>Subscription Plans</h1>
                <p>Choose the perfect plan for your LPG business</p>
            </div>

            {error && (
                <Alert type="error" className="mb-4">
                    {error}
                </Alert>
            )}

            {/* Current Subscription Status */}
            {subscription && (
                <div className="current-subscription">
                    <h2>Current Subscription</h2>
                    <Card className="subscription-card">
                        <div className="subscription-info">
                            <div className="subscription-details">
                                <h3>{subscription.plan_name}</h3>
                                <Badge 
                                    color={getStatusColor(subscription.subscription_status)}
                                    className="status-badge"
                                >
                                    {subscription.subscription_status.toUpperCase()}
                                </Badge>
                                <p className="subscription-price">
                                                                         €{subscription.base_amount}/{subscription.billing_cycle}
                                </p>
                                <p className="subscription-dates">
                                    Started: {new Date(subscription.start_date).toLocaleDateString()}
                                    {subscription.trial_end && (
                                        <span className="trial-info">
                                            Trial ends: {new Date(subscription.trial_end).toLocaleDateString()}
                                        </span>
                                    )}
                                </p>
                            </div>
                        </div>
                    </Card>
                </div>
            )}

            {/* Usage Summary */}
            {usage && (
                <div className="usage-summary">
                    <h2>Usage Summary</h2>
                    <div className="usage-grid">
                        {Object.entries(usage.usage).map(([key, data]) => (
                            <Card key={key} className="usage-card">
                                <h4>{key.charAt(0).toUpperCase() + key.slice(1)}</h4>
                                <div className="usage-stats">
                                    <span className="usage-current">{data.current}</span>
                                    <span className="usage-separator">/</span>
                                    <span className="usage-limit">{data.limit}</span>
                                </div>
                                <div className="usage-bar">
                                    <div 
                                        className={`usage-progress usage-${getUsageColor(data.percentage)}`}
                                        style={{ width: `${data.percentage}%` }}
                                    ></div>
                                </div>
                                <span className="usage-percentage">{data.percentage.toFixed(1)}%</span>
                            </Card>
                        ))}
                    </div>
                </div>
            )}

            {/* Available Plans */}
            <div className="plans-section">
                <h2>Available Plans</h2>
                <div className="plans-grid">
                    {plans.map((plan) => (
                        <Card 
                            key={plan.id} 
                            className={`plan-card ${selectedPlan?.id === plan.id ? 'selected' : ''}`}
                            onClick={() => handlePlanSelect(plan)}
                        >
                            <div className="plan-header">
                                <h3>{plan.plan_name}</h3>
                                <Badge color="primary" className="plan-tier">
                                    {plan.plan_tier.toUpperCase()}
                                </Badge>
                            </div>
                            
                            <div className="plan-price">
                                                                 <span className="price-amount">€{plan.base_amount}</span>
                                <span className="price-period">/{plan.billing_cycle}</span>
                            </div>
                            
                            <p className="plan-description">{plan.description}</p>
                            
                            <div className="plan-features">
                                <h4>Features:</h4>
                                <ul>
                                    {plan.features.map((feature, index) => (
                                        <li key={index}>{feature}</li>
                                    ))}
                                </ul>
                            </div>
                            
                            <div className="plan-limits">
                                <h4>Limits:</h4>
                                <div className="limits-grid">
                                    <div className="limit-item">
                                        <span className="limit-label">Orders/month:</span>
                                        <span className="limit-value">{plan.max_orders_per_month.toLocaleString()}</span>
                                    </div>
                                    <div className="limit-item">
                                        <span className="limit-label">Active drivers:</span>
                                        <span className="limit-value">{plan.max_active_drivers}</span>
                                    </div>
                                    <div className="limit-item">
                                        <span className="limit-label">Storage:</span>
                                        <span className="limit-value">{plan.max_storage_gb} GB</span>
                                    </div>
                                    <div className="limit-item">
                                        <span className="limit-label">API calls/min:</span>
                                        <span className="limit-value">{plan.max_api_requests_per_minute}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <Button 
                                className="select-plan-btn"
                                color={selectedPlan?.id === plan.id ? 'success' : 'primary'}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handlePlanSelect(plan);
                                }}
                            >
                                {selectedPlan?.id === plan.id ? 'Selected' : 'Select Plan'}
                            </Button>
                        </Card>
                    ))}
                </div>
            </div>

            {/* Subscribe Button */}
            {selectedPlan && !subscription && (
                <div className="subscribe-section">
                    <Card className="subscribe-card">
                        <h3>Ready to Subscribe?</h3>
                                                 <p>You've selected the <strong>{selectedPlan.plan_name}</strong> plan for €{selectedPlan.base_amount}/{selectedPlan.billing_cycle}</p>
                        <div className="subscribe-actions">
                            <Button 
                                color="success" 
                                size="large"
                                onClick={handleSubscribe}
                                disabled={loading}
                            >
                                {loading ? 'Creating Subscription...' : 'Subscribe Now'}
                            </Button>
                            <Button 
                                color="secondary" 
                                onClick={() => setSelectedPlan(null)}
                                disabled={loading}
                            >
                                Cancel
                            </Button>
                        </div>
                    </Card>
                </div>
            )}

            {/* Upgrade/Downgrade Section */}
            {selectedPlan && subscription && (
                <div className="subscribe-section">
                    <Card className="subscribe-card">
                        <h3>Upgrade Your Subscription</h3>
                        <p>You currently have the <strong>{subscription.plan_name}</strong> plan. Upgrade to <strong>{selectedPlan.plan_name}</strong> for €{selectedPlan.base_amount}/{selectedPlan.billing_cycle}</p>
                        <div className="subscribe-actions">
                            <Button 
                                color="success" 
                                size="large"
                                onClick={handleSubscribe}
                                disabled={loading}
                            >
                                {loading ? 'Upgrading...' : 'Upgrade Now'}
                            </Button>
                            <Button 
                                color="secondary" 
                                onClick={() => setSelectedPlan(null)}
                                disabled={loading}
                            >
                                Cancel
                            </Button>
                        </div>
                    </Card>
                </div>
            )}
        </div>
    );
};

export default Subscriptions; 