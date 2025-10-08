// Header component with search functionality
import React, { useEffect, useRef, useCallback } from 'react';
import { useUIMemoryDispatch } from '../memory/ui_memory';
import { useSearchMemoryState, useSearchMemoryDispatch } from '../memory/search_memory';
import '../css_design/components/Layout/Header.css';

// Main header component
const TopBar = React.memo(() => {
  const uiDispatch = useUIMemoryDispatch();
  const { query } = useSearchMemoryState();
  const { setQuery, clearSearch } = useSearchMemoryDispatch();
  const searchInputRef = useRef(null);

  const handleMenuToggle = useCallback(() => {
    uiDispatch({ type: 'TOGGLE_SIDEBAR' });
  }, [uiDispatch]);

  const handleSearch = useCallback((e) => {
    setQuery(e.target.value);
  }, [setQuery]);

  const handleClearSearch = useCallback(() => {
    clearSearch();
  }, [clearSearch]);

  useEffect(() => {
    const handleKeyPress = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        searchInputRef.current?.focus();
        return;
      }
      const activeElement = document.activeElement;
      const isTypingInInput = activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.tagName === 'SELECT' ||
        activeElement.contentEditable === 'true'
      );
      if (event.ctrlKey || event.altKey || event.metaKey || event.shiftKey) {
        return;
      }
      if (event.key.length > 1 && !['Backspace', 'Delete'].includes(event.key)) {
        return;
      }
      if (!isTypingInInput && searchInputRef.current) {
        searchInputRef.current.focus();
        if (event.key.length === 1) {
          setQuery(query + event.key);
        }
        else if (event.key === 'Backspace') {
          setQuery(query.slice(0, -1));
        }
      }
    };
    document.addEventListener('keydown', handleKeyPress);
    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [query, setQuery]);

  return (
    <header className="modern-header">
      <div className="modern-header__container">
        {/* Left side */}
        <div className="modern-header__left">
          <button
            className="modern-header__menu-btn"
            onClick={handleMenuToggle}
            aria-label="Toggle sidebar"
          >
            <span className="material-icons">menu</span>
          </button>
          <div className="modern-header__brand">
            <div className="modern-header__logo">
              <span className="material-icons">event_note</span>
            </div>
            <div className="modern-header__brand-text">
              <span className="modern-header__title">Absence</span>
              <span className="modern-header__subtitle">Management</span>
            </div>
          </div>
        </div>
        
        {/* Center - Search */}
        <div className="modern-header__center">
          <div className="modern-header__search">
            <div className="modern-header__search-icon">
              <span className="material-icons">search</span>
            </div>
            <input
              ref={searchInputRef}
              type="text"
              className="modern-header__search-input"
              placeholder="Search employees, departments..."
              value={query}
              onChange={handleSearch}
            />
            {query && (
              <button
                className="modern-header__search-clear"
                onClick={handleClearSearch}
                title="Clear search"
              >
                <span className="material-icons">clear</span>
              </button>
            )}
            <div className="modern-header__search-shortcut">
              <span>⌘K</span>
            </div>
          </div>
        </div>
        
        {/* Right side */}
        <div className="modern-header__right">
          {/* Action buttons - just icons without functionality */}
          <div className="modern-header__actions">
            <button
              className="modern-header__action-btn"
              aria-label="Dark mode (coming soon)"
              title="Dark mode (coming soon)"
            >
              <span className="material-icons">dark_mode</span>
            </button>
            <div className="modern-header__notifications">
              <button
                className="modern-header__action-btn modern-header__notification-btn"
                aria-label="Notifications (coming soon)"
                title="Notifications (coming soon)"
              >
                <span className="material-icons">notifications_none</span>
              </button>
            </div>
          </div>
          
          {/* Profile */}
          <div className="modern-header__profile">
            <button className="modern-header__profile-btn">
              <div className="modern-header__avatar">
                <span>MJ</span>
                <div className="modern-header__status-indicator"></div>
              </div>
              <div className="modern-header__user-info">
                <span className="modern-header__user-name">manju</span>
                <span className="modern-header__user-role">Administrator</span>
              </div>
              <span className="material-icons modern-header__dropdown-icon">expand_more</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
});

export default TopBar;