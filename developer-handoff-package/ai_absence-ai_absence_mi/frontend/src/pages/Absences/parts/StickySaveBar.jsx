// Bottom save/export/email bar
import React from 'react';
import EmailModal from '../../../email_component/EmailModal';

const StickySaveBar = React.memo(({
  hasChanges,
  recentChanges,
  isLoading,
  isExporting,
  isLoadingEmail,
  showEmailModal,
  employees,
  selectedMonth,
  onSaveChanges,
  onRevertChanges,
  onExportToExcel,
  onSendEmail,
  onOpenEmailModal,
  onCloseEmailModal
}) => {
  // Don't show the bar if there are no changes
  if (!hasChanges && recentChanges.length === 0) {
    return null;
  }

  return (
    <>
      <div className="sticky-save-bar" style={{
        position: 'fixed',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '16px 24px',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.15)',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        zIndex: 1000,
        backdropFilter: 'blur(10px)'
      }}>
        {/* Changes count */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: '#374151',
          fontSize: '14px',
          fontWeight: '600'
        }}>
          <span className="material-icons" style={{ fontSize: '18px', color: '#f59e0b' }}>
            edit
          </span>
          {recentChanges.length} unsaved changes
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <button 
            className="glass-btn glass-btn--success"
            onClick={onSaveChanges}
            disabled={!hasChanges || isLoading}
            title="Save all changes"
          >
            {isLoading ? 'Saving...' : 'Save Changes'}
            <div className="btn-glow"></div>
          </button>
        </div>

        {/* Close button */}
        <button 
          onClick={onRevertChanges}
          disabled={isLoading}
          title="Discard all changes and close"
          style={{
            background: 'none',
            border: 'none',
            color: '#6b7280',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
            fontSize: '18px'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = '#f3f4f6';
            e.target.style.color = '#374151';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'none';
            e.target.style.color = '#6b7280';
          }}
        >
          <span className="material-icons">close</span>
        </button>
      </div>

      {/* Email Modal */}
      {showEmailModal && (
        <EmailModal
          isOpen={showEmailModal}
          onClose={onCloseEmailModal}
          onSendEmail={onSendEmail}
          employees={employees}
          isLoading={isLoadingEmail}
          recentChanges={recentChanges}
          selectedMonth={selectedMonth}
        />
      )}
    </>
  );
});

StickySaveBar.displayName = 'StickySaveBar';

export default StickySaveBar;