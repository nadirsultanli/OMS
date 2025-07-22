// Helper function to extract user-friendly error messages from API responses
export const extractErrorMessage = (errorData) => {
  if (!errorData) {
    return null;
  }
  
  // If it's a simple string message
  if (typeof errorData === 'string') {
    return errorData;
  }
  
  // If it's a simple object with detail
  if (errorData.detail && typeof errorData.detail === 'string') {
    return errorData.detail;
  }
  
  // If it's FastAPI validation errors (array of error objects)
  if (Array.isArray(errorData.detail)) {
    const messages = errorData.detail.map(err => {
      const field = err.loc ? err.loc.join(' -> ') : 'Field';
      return `${field}: ${err.msg}`;
    });
    return messages.join(', ');
  }
  
  // If it's a single validation error object
  if (errorData.detail && typeof errorData.detail === 'object') {
    return JSON.stringify(errorData.detail);
  }
  
  // Fallback
  return 'An error occurred';
};