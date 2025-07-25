import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Search } from 'lucide-react';
import './SearchableDropdown.css';

const SearchableDropdown = ({ 
  options = [], 
  value, 
  onChange, 
  placeholder = 'Select an option',
  searchPlaceholder = 'Search...',
  className = '',
  name = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef(null);
  const searchInputRef = useRef(null);

  // Filter options based on search term
  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get the selected option label
  const selectedOption = options.find(opt => opt.value === value);
  const displayText = selectedOption ? selectedOption.label : placeholder;

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const handleSelect = (optionValue) => {
    onChange({ target: { name, value: optionValue } });
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleDropdownClick = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className={`searchable-dropdown ${className}`} ref={dropdownRef}>
      <div 
        className={`dropdown-header ${isOpen ? 'open' : ''}`}
        onClick={handleDropdownClick}
      >
        <span className={`dropdown-value ${!selectedOption ? 'placeholder' : ''}`}>
          {displayText}
        </span>
        <ChevronDown className={`dropdown-icon ${isOpen ? 'rotate' : ''}`} size={20} />
      </div>
      
      {isOpen && (
        <div className="dropdown-menu">
          <div className="dropdown-search">
            <Search size={16} className="search-icon" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={searchPlaceholder}
              className="dropdown-search-input"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
          
          <div className="dropdown-options">
            {/* Show "All" option if there's an empty value option */}
            {options.some(opt => opt.value === '') && (
              <div
                className={`dropdown-option ${value === '' ? 'selected' : ''}`}
                onClick={() => handleSelect('')}
              >
                {options.find(opt => opt.value === '').label}
              </div>
            )}
            
            {filteredOptions.length > 0 ? (
              filteredOptions
                .filter(option => option.value !== '')
                .map((option) => (
                  <div
                    key={option.value}
                    className={`dropdown-option ${value === option.value ? 'selected' : ''}`}
                    onClick={() => handleSelect(option.value)}
                  >
                    {option.label}
                  </div>
                ))
            ) : (
              <div className="dropdown-no-results">No results found</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchableDropdown;