// Utility function to extract user-friendly error messages from backend responses
export const extractErrorMessage = (errorData) => {
  if (!errorData) {
    return 'An error occurred';
  }
  
  // If it's already a string, return it
  if (typeof errorData === 'string') {
    return errorData;
  }
  
  // If it's an array of validation errors (FastAPI validation format)
  if (Array.isArray(errorData)) {
    const messages = errorData.map(err => {
      const field = err.loc ? err.loc.join(' -> ') : 'Field';
      return `${field}: ${err.msg}`;
    });
    return messages.join(', ');
  }
  
  // If it's an object with a detail property
  if (errorData.detail) {
    return extractErrorMessage(errorData.detail);
  }
  
  // If it's a validation error object
  if (errorData.msg) {
    const field = errorData.loc ? errorData.loc.join(' -> ') : '';
    return field ? `${field}: ${errorData.msg}` : errorData.msg;
  }
  
  // If it's an object with message property
  if (errorData.message) {
    return errorData.message;
  }
  
  // Fallback to JSON.stringify but only show a user-friendly message
  return 'Invalid input provided. Please check your data and try again.';
};

// Helper function to handle API error responses consistently
export const handleApiError = (error) => {
  if (error?.response?.data) {
    return extractErrorMessage(error.response.data);
  }
  
  if (error?.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred. Please try again.';
};