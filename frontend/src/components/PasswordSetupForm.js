import React, { useState } from 'react';
import verificationService from '../services/verificationService';

const PasswordSetupForm = ({ 
  onSubmit, 
  isLoading, 
  errors, 
  title = "Set Your Password",
  description = "Create a secure password for your account",
  buttonText = "Set Password",
  loadingText = "Setting Password...",
  showEmail = false,
  email = '',
  onEmailChange = null
}) => {
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  });
  const [localErrors, setLocalErrors] = useState({});
  const [passwordValidation, setPasswordValidation] = useState({
    isValid: false,
    errors: []
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear specific field error when user starts typing
    if (localErrors[name]) {
      setLocalErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Real-time password validation
    if (name === 'password') {
      const validation = verificationService.validatePassword(value);
      setPasswordValidation(validation);
    }

    // Check password match in real-time
    if (name === 'confirmPassword' || (name === 'password' && formData.confirmPassword)) {
      const passwordToCheck = name === 'password' ? value : formData.password;
      const confirmPasswordToCheck = name === 'confirmPassword' ? value : formData.confirmPassword;
      
      if (confirmPasswordToCheck && !verificationService.validatePasswordMatch(passwordToCheck, confirmPasswordToCheck)) {
        setLocalErrors(prev => ({
          ...prev,
          confirmPassword: 'Passwords do not match'
        }));
      } else if (confirmPasswordToCheck) {
        setLocalErrors(prev => ({
          ...prev,
          confirmPassword: ''
        }));
      }
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else {
      const passwordValidation = verificationService.validatePassword(formData.password);
      if (!passwordValidation.isValid) {
        newErrors.password = passwordValidation.errors[0]; // Show first error
      }
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (!verificationService.validatePasswordMatch(formData.password, formData.confirmPassword)) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setLocalErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData.password, formData.confirmPassword);
    }
  };

  const allErrors = { ...localErrors, ...errors };

  return (
    <>
      <div className="verification-header">
        <h1 className="verification-title">{title}</h1>
        <p className="verification-description">{description}</p>
      </div>

      <form onSubmit={handleSubmit} className="verification-form">
        {showEmail && (
          <div className="form-group">
            <label htmlFor="email" className="form-label">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={email}
              onChange={(e) => onEmailChange && onEmailChange(e.target.value)}
              className={`form-input ${errors.email ? 'error' : ''}`}
              placeholder="Enter your email address"
              disabled={isLoading}
            />
            {/* Remove error message display */}
          </div>
        )}
        
        <div className="form-group">
          <label htmlFor="password" className="form-label">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            className={`form-input ${allErrors.password ? 'error' : ''}`}
            placeholder="Enter your password"
            disabled={isLoading}
          />
          {/* Remove error message display */}
          
          {/* Password requirements */}
          {formData.password && (
            <div className="password-requirements">
              <p className="requirements-title">Password must contain:</p>
              <ul className="requirements-list">
                <li className={formData.password.length >= 8 ? 'valid' : 'invalid'}>
                  At least 8 characters
                </li>
                <li className={/[A-Z]/.test(formData.password) ? 'valid' : 'invalid'}>
                  One uppercase letter
                </li>
                <li className={/[0-9]/.test(formData.password) ? 'valid' : 'invalid'}>
                  One number
                </li>
                <li className={/[!@#$%^&*(),.?":{}|<>]/.test(formData.password) ? 'valid' : 'invalid'}>
                  One special character
                </li>
              </ul>
            </div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleInputChange}
            className={`form-input ${allErrors.confirmPassword ? 'error' : ''}`}
            placeholder="Confirm your password"
            disabled={isLoading}
          />
          {/* Remove error message display */}
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="verification-button"
            disabled={isLoading || !passwordValidation.isValid || !formData.confirmPassword || !verificationService.validatePasswordMatch(formData.password, formData.confirmPassword)}
          >
            {isLoading ? loadingText : buttonText}
          </button>
        </div>
      </form>
    </>
  );
};

export default PasswordSetupForm;