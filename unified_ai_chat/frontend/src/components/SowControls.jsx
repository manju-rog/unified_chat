import React, { useState } from "react";

/**
 * Clean SOW Controls - Single source of truth for actions
 */
export default function SowControls({ hint, onClick }) {
  const [selectedContact, setSelectedContact] = useState(null);
  const [resourceCounts, setResourceCounts] = useState({});

  if (!hint) return null;

  const handleContactSelect = (contact) => {
    setSelectedContact(contact);
    onClick(contact.value);
  };

  const getResourceCount = (role) => {
    const resource = hint.current_resources?.find(r => r.role === role);
    return resource ? resource.count : 0;
  };

  // Resource management
  const updateResourceCount = (role, delta) => {
    const currentCount = getResourceCount(role);
    const newCount = Math.max(0, currentCount + delta);
    onClick(`${delta > 0 ? '+' : '-'}:${role}`);
  };

  // Generate resource summary for "Add Resources" button
  const generateResourceSummary = () => {
    const resources = hint.current_resources || [];
    if (resources.length === 0) return "Add resources to the project";
    
    const summary = resources
      .filter(r => r.count > 0)
      .map(r => `${r.count} ${r.role}${r.count > 1 ? 's' : ''}`)
      .join(", ");
    
    return `Add these resources: ${summary}`;
  };

  const hasResources = () => {
    const resources = hint.current_resources || [];
    return resources.some(r => r.count > 0);
  };

  return (
    <div style={{ 
      display: "flex", 
      flexDirection: "column", 
      gap: 12, 
      padding: "16px",
      backgroundColor: "white",
      borderRadius: "8px",
      border: "1px solid #e0e0e0"
    }}>
      
      {/* Clean Services Toggle - Standard vs Custom */}
      {hint.service_selection && (
        <div style={{ display: "flex", gap: "8px" }}>
          {["standard", "custom"].map(option => {
            const isActive = hint.selected_service === option;
            return (
              <button
                key={option}
                onClick={() => onClick(option)}
                style={{
                  flex: 1,
                  padding: "12px 20px",
                  borderRadius: "4px",
                  border: "1px solid",
                  borderColor: isActive ? "#000" : "#d0d0d0",
                  backgroundColor: isActive ? "#000" : "white",
                  color: isActive ? "white" : "#333",
                  fontSize: "14px",
                  fontWeight: "500",
                  cursor: "pointer",
                  transition: "all 0.2s ease"
                }}
                onMouseOver={(e) => {
                  if (!isActive) {
                    e.target.style.borderColor = "#000";
                  }
                }}
                onMouseOut={(e) => {
                  if (!isActive) {
                    e.target.style.borderColor = "#d0d0d0";
                  }
                }}
              >
                {option === "standard" ? "Standard Package" : "Custom Services"}
              </button>
            );
          })}
        </div>
      )}

      {/* Regular Action Buttons (non-resource, non-service) - Show only once */}
      {hint.confirmation_buttons && !hint.show_resource_builder && !hint.service_selection && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {hint.confirmation_buttons.slice(0, hint.confirmation_buttons.length > 2 ? 3 : hint.confirmation_buttons.length).map((b) => (
            <button 
              key={b.id} 
              onClick={() => onClick(b.populate_input || b.value)}
              style={{
                padding: "10px 20px",
                borderRadius: "4px",
                border: "1px solid #d0d0d0",
                backgroundColor: "white",
                color: "#333",
                fontSize: "14px",
                fontWeight: "500",
                cursor: "pointer",
                transition: "all 0.2s"
              }}
              onMouseOver={(e) => {
                e.target.style.borderColor = "#000";
                e.target.style.backgroundColor = "#f5f5f5";
              }}
              onMouseOut={(e) => {
                e.target.style.borderColor = "#d0d0d0";
                e.target.style.backgroundColor = "white";
              }}
            >
              {b.label.replace(/📦|🛠️|📄|✅|⚠️/g, '').trim()}
            </button>
          ))}
        </div>
      )}

      {/* Clean Resource Picker with + / - / count */}
      {hint.show_resource_builder && (
        <div style={{ 
          backgroundColor: "white", 
          padding: "16px", 
          borderRadius: "4px",
          border: "1px solid #e0e0e0"
        }}>
          
          {/* Resource Grid - Clean 2x3 layout */}
          <div style={{ 
            display: "grid", 
            gridTemplateColumns: "repeat(2, 1fr)", 
            gap: "12px", 
            marginBottom: "16px"
          }}>
            {hint.resource_roles?.map((role) => {
              const count = getResourceCount(role);
              return (
                <div key={role} style={{ 
                  display: "flex", 
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px",
                  backgroundColor: count > 0 ? "#f5f5f5" : "white",
                  borderRadius: "4px",
                  border: `1px solid ${count > 0 ? "#000" : "#e0e0e0"}`,
                  transition: "all 0.2s ease"
                }}>
                  <div style={{ 
                    fontWeight: "500", 
                    fontSize: "14px", 
                    color: "#333"
                  }}>
                    {role}
                  </div>
                  
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <button 
                      onClick={() => updateResourceCount(role, -1)}
                      disabled={count === 0}
                      style={{
                        width: "28px",
                        height: "28px",
                        borderRadius: "4px",
                        border: "1px solid #d0d0d0",
                        backgroundColor: count > 0 ? "white" : "#f5f5f5",
                        color: "#333",
                        cursor: count > 0 ? "pointer" : "not-allowed",
                        fontSize: "16px",
                        fontWeight: "bold",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        transition: "all 0.2s ease"
                      }}
                    >
                      −
                    </button>
                    <span style={{ 
                      minWidth: "24px", 
                      textAlign: "center", 
                      fontWeight: "600",
                      fontSize: "14px",
                      color: "#333"
                    }}>
                      {count}
                    </span>
                    <button 
                      onClick={() => updateResourceCount(role, 1)}
                      style={{
                        width: "28px",
                        height: "28px",
                        borderRadius: "4px",
                        border: "1px solid #000",
                        backgroundColor: "white",
                        color: "#333",
                        cursor: "pointer",
                        fontSize: "16px",
                        fontWeight: "bold",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        transition: "all 0.2s ease"
                      }}
                    >
                      +
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Single "Add Resources" Button with Dynamic Summary */}
          <div style={{ display: "flex", justifyContent: "center" }}>
            <button 
              onClick={() => {
                const summary = generateResourceSummary();
                const inputElement = document.querySelector('input[type="text"], textarea');
                if (inputElement) {
                  inputElement.value = summary;
                  inputElement.dispatchEvent(new Event('input', { bubbles: true }));
                  inputElement.focus();
                }
              }}
              disabled={!hasResources()}
              style={{
                padding: "10px 24px",
                borderRadius: "4px",
                border: "none",
                backgroundColor: hasResources() ? "#000" : "#e0e0e0",
                color: hasResources() ? "white" : "#999",
                fontSize: "14px",
                fontWeight: "500",
                cursor: hasResources() ? "pointer" : "not-allowed",
                transition: "all 0.2s ease"
              }}
              onMouseOver={(e) => {
                if (hasResources()) {
                  e.target.style.backgroundColor = "#333";
                }
              }}
              onMouseOut={(e) => {
                if (hasResources()) {
                  e.target.style.backgroundColor = "#000";
                }
              }}
            >
              Add Resources
            </button>
          </div>
        </div>
      )}

      {/* Contact Dropdown - Show only first 3 */}
      {hint.contact_dropdown && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {hint.contact_dropdown.slice(0, 3).map((contact) => (
            <div 
              key={contact.id}
              onClick={() => handleContactSelect(contact)}
              style={{
                padding: "12px",
                border: "1px solid",
                borderColor: selectedContact?.id === contact.id ? "#000" : "#e0e0e0",
                borderRadius: "4px",
                cursor: "pointer",
                transition: "all 0.2s",
                backgroundColor: selectedContact?.id === contact.id ? "#f5f5f5" : "white"
              }}
              onMouseOver={(e) => {
                if (selectedContact?.id !== contact.id) {
                  e.target.style.borderColor = "#000";
                }
              }}
              onMouseOut={(e) => {
                if (selectedContact?.id !== contact.id) {
                  e.target.style.borderColor = "#e0e0e0";
                }
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ margin: "0 0 4px 0", color: "#333", fontSize: "14px", fontWeight: "500" }}>
                    {contact.details.name}
                  </div>
                  <div style={{ margin: "0", color: "#666", fontSize: "12px" }}>
                    {contact.details.contact_person} • {contact.details.email}
                  </div>
                </div>
                <span style={{
                  padding: "4px 8px",
                  backgroundColor: "#f5f5f5",
                  color: "#333",
                  borderRadius: "4px",
                  fontSize: "11px",
                  fontWeight: "500",
                  border: "1px solid #e0e0e0"
                }}>
                  {contact.details.type.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Generate Button - Show only once */}
      {hint.generate_buttons && (
        <div style={{ display: "flex", justifyContent: "center" }}>
          <button 
            onClick={() => onClick(hint.generate_buttons[0].value)}
            style={{
              padding: "12px 32px",
              backgroundColor: "#000",
              color: "white",
              border: "none",
              borderRadius: "4px",
              fontSize: "14px",
              fontWeight: "500",
              cursor: "pointer",
              transition: "all 0.2s"
            }}
            onMouseOver={(e) => {
              e.target.style.backgroundColor = "#333";
            }}
            onMouseOut={(e) => {
              e.target.style.backgroundColor = "#000";
            }}
          >
            {hint.generate_buttons[0].label.replace(/📄|✅/g, '').trim()}
          </button>
        </div>
      )}
    </div>
  );
}