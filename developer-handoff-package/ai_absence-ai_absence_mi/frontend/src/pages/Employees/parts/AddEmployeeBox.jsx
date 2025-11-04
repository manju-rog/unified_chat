// Add employee modal (super simple)
import React, { useState, useCallback, useMemo } from 'react';
import { useDataMemoryState, useDataMemoryDispatch } from '../../../memory/data_memory';
import api from '../../../services/api';
import '../../../css_design/components/UI/AddEmployeeModal.css';

// Employee creation modal component
const AddEmployeeBox = React.memo(({ isOpen, onClose, onSuccess }) => {
  const { departments, locations, roles } = useDataMemoryState();
  const { addEmployee } = useDataMemoryDispatch();

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    department: '',
    role: '',
    location: '',
    manager: '',
    joinDate: '',
    employeeId: '',
    systemName: '',
    systemIP: ''
  });

  // Form status tracking
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState('');

  // Memoized validation rules to prevent recreation on every render
  const validationRules = useMemo(() => ({
    emailRegex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    phoneRegex: /^[+]?[0-9\-\s()]+$/,
    minEmployeeIdLength: 2
  }), []);

  // Memoized form validity check to prevent unnecessary recalculations
  const isFormValid = useMemo(() => {
    return formData.name.trim() && 
           formData.email.trim() && 
           formData.department && 
           formData.role && 
           formData.location &&
           Object.keys(errors).length === 0;
  }, [formData.name, formData.email, formData.department, formData.role, formData.location, errors]);

  // Handle form input changes with optimized error clearing
  const handleInputChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear field error only if it exists to prevent unnecessary state updates
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  }, [errors]);

  const validateForm = useCallback(() => {
    const newErrors = {};
    
    // Required field validations
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!formData.department) newErrors.department = 'Department is required';
    if (!formData.role) newErrors.role = 'Role is required';
    if (!formData.location) newErrors.location = 'Location is required';
    
    // Email format validation using memoized regex
    if (formData.email && !validationRules.emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    // Phone format validation using memoized regex
    if (formData.phone && !validationRules.phoneRegex.test(formData.phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }
    
    // Employee ID length validation using memoized rule
    if (formData.employeeId && formData.employeeId.trim().length < validationRules.minEmployeeIdLength) {
      newErrors.employeeId = 'Employee ID must be at least 2 characters';
    }
    
    // Join date validation
    if (formData.joinDate) {
      const joinDate = new Date(formData.joinDate);
      const today = new Date();
      if (joinDate > today) {
        newErrors.joinDate = 'Join date cannot be in the future';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, validationRules]);

  const generateRandomData = useCallback((data) => {
    const randomData = { ...data };
    if (!randomData.phone || randomData.phone.trim() === '') {
      randomData.phone = `+1-${Math.floor(Math.random() * 900 + 100)}-${Math.floor(Math.random() * 900 + 100)}-${Math.floor(Math.random() * 9000 + 1000)}`;
    }
    if (!randomData.employeeId || randomData.employeeId.trim() === '') {
      randomData.employeeId = `EMP${Math.floor(Math.random() * 90000 + 10000)}`;
    }
    if (!randomData.manager || randomData.manager.trim() === '') {
      const managers = ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Lisa Wilson', 'David Brown'];
      randomData.manager = managers[Math.floor(Math.random() * managers.length)];
    }
    if (!randomData.joinDate || randomData.joinDate.trim() === '') {
      const today = new Date();
      const twoYearsAgo = new Date(today.getFullYear() - 2, today.getMonth(), today.getDate());
      const randomTime = twoYearsAgo.getTime() + Math.random() * (today.getTime() - twoYearsAgo.getTime());
      const randomDate = new Date(randomTime);
      // Use timezone-safe date formatting to avoid +1 day issue
      randomData.joinDate = `${randomDate.getFullYear()}-${String(randomDate.getMonth() + 1).padStart(2, '0')}-${String(randomDate.getDate()).padStart(2, '0')}`;
    }
    if (!randomData.systemName || randomData.systemName.trim() === '') {
      const prefixes = ['DESK', 'LAP', 'WS', 'PC'];
      const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
      randomData.systemName = `${prefix}-${Math.floor(Math.random() * 9000 + 1000)}`;
    }
    if (!randomData.systemIP || randomData.systemIP.trim() === '') {
      randomData.systemIP = `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;
    }
    return randomData;
  }, []);

  const handleClose = useCallback(() => {
    setFormData({
      name: '',
      email: '',
      phone: '',
      department: '',
      role: '',
      location: '',
      manager: '',
      joinDate: '',
      employeeId: '',
      systemName: '',
      systemIP: ''
    });
    setErrors({});
    setSubmitError('');
    onClose();
  }, [onClose]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      return;
    }
    setIsSubmitting(true);
    setSubmitError('');
    const processedFormData = generateRandomData(formData);
    try {
      const newEmployee = await api.employees.create(processedFormData);
      addEmployee(newEmployee);
      onSuccess && onSuccess(newEmployee);
      handleClose();
    } catch (error) {
      console.error('Failed to create employee:', error);
      const errorMessage = api.utils.handleError(error);
      if (errorMessage.includes('Cannot connect to server')) {
        setSubmitError(
          `${errorMessage}\n\nTo start the backend:\n1. Open terminal\n2. Navigate to: absence-management-backend\n3. Run: mvn spring-boot:run\n4. Wait for "Started Application" message\n5. Try adding employee again`
        );
      } else {
        setSubmitError(errorMessage);
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validateForm, generateRandomData, addEmployee, onSuccess, handleClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={handleClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>➕ Add New Employee</h2>
          <button className="modal-close-btn" onClick={handleClose}>
            <span className="material-icons">close</span>
          </button>
        </div>
        
        <div className="modal-body">
          <form onSubmit={handleSubmit} className="employee-form">
            {submitError && (
              <div className="error-message">
                <span className="material-icons">error</span>
                <div className="error-text">
                  {submitError.split('\n').map((line, index) => (
                    <div key={index}>{line}</div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="form-section">
              <h3>👤 Basic Information</h3>
              <div className="form-helper-text">
                <span className="material-icons">info</span>
                Empty optional fields will be automatically filled with sample data
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="name">Full Name *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className={errors.name ? 'error' : ''}
                    placeholder="Enter full name"
                  />
                  {errors.name && <span className="field-error">{errors.name}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="email">Email Address *</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className={errors.email ? 'error' : ''}
                    placeholder="Enter email address"
                  />
                  {errors.email && <span className="field-error">{errors.email}</span>}
                </div>
              </div>
            </div>
            
            <div className="form-section">
              <h3>🏢 Work Information</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="department">Department *</label>
                  <select
                    id="department"
                    name="department"
                    value={formData.department}
                    onChange={handleInputChange}
                    className={errors.department ? 'error' : ''}
                  >
                    <option value="">Select Department</option>
                    {departments.map(dept => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                  {errors.department && <span className="field-error">{errors.department}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="role">Role *</label>
                  <select
                    id="role"
                    name="role"
                    value={formData.role}
                    onChange={handleInputChange}
                    className={errors.role ? 'error' : ''}
                  >
                    <option value="">Select Role</option>
                    {roles.map(role => (
                      <option key={role} value={role}>{role}</option>
                    ))}
                  </select>
                  {errors.role && <span className="field-error">{errors.role}</span>}
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="location">Location *</label>
                  <select
                    id="location"
                    name="location"
                    value={formData.location}
                    onChange={handleInputChange}
                    className={errors.location ? 'error' : ''}
                  >
                    <option value="">Select Location</option>
                    {locations.map(location => (
                      <option key={location} value={location}>{location}</option>
                    ))}
                  </select>
                  {errors.location && <span className="field-error">{errors.location}</span>}
                </div>
              </div>
            </div>
          </form>
        </div>
        
        <div className="modal-footer">
          <button 
            type="button" 
            className="glass-btn glass-btn--secondary" 
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
            <div className="btn-glow"></div>
          </button>
          <button 
            type="submit" 
            className="glass-btn glass-btn--primary" 
            onClick={handleSubmit}
            disabled={isSubmitting || !isFormValid}
          >
            {isSubmitting ? 'Creating...' : 'Add Employee'}
            <div className="btn-glow"></div>
          </button>
        </div>
      </div>
    </div>
  );
});

AddEmployeeBox.displayName = 'AddEmployeeBox';

export default AddEmployeeBox;