// Reusable button component
import React from 'react';
import '../css_design/components/UI/Button.css';

const Button = React.memo(({
  children,                 // 📝 Text or content inside the button
  variant = 'primary',      // 🌈 Color theme (primary, secondary, success, warning, danger)
  size = 'md',             // 📏 Button size (sm, md, lg)
  disabled = false,        // 🚫 Whether button is clickable or not
  onClick,                 // 🖱️ Function to run when button is clicked
  type = 'button',         // 🔧 HTML button type (button, submit, reset)
  className = '',          // 🎨 Extra CSS classes if needed
  ...props                 // 🔧 Any other HTML button properties
}) => {
  const buttonClass = `btn btn--${variant} btn--${size} ${className}`;
  return (
    <button
      type={type}
      className={buttonClass}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;