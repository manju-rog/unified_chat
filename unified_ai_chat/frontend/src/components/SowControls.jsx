import React, { useState } from "react";

/**
 * Enhanced SOW Controls with beautiful UI elements
 */
export default function SowControls({ hint, onClick }) {
  const [selectedContact, setSelectedContact] = useState(null);

  if (!hint) return null;

  const handleContactSelect = (contact) => {
    setSelectedContact(contact);
    onClick(contact.value);
  };

  const getResourceCount = (role) => {
    const resource = hint.current_resources?.find(r => r.role === role);
    return resource ? resource.count : 0;
  };

  return (
    <div style={{ 
      display: "flex", 
      flexDirection: "column", 
      gap: 16, 
      padding: "16px",
      backgroundColor: "#f8f9fa",
      borderRadius: "12px",
      border: "1px solid #e9ecef"
    }}>
      
      {/* Service Selection Buttons */}
      {hint.confirmation_buttons && (
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {hint.confirmation_buttons.map((b) => (
            <button 
              key={b.id} 
              onClick={() => onClick(b.value)}
              style={{
                padding: "12px 24px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: b.style === "primary" ? "#007bff" : "#6c757d",
                color: "white",
                fontSize: "14px",
                fontWeight: "500",
                cursor: "pointer",
                transition: "all 0.2s",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}
              onMouseOver={(e) => {
                e.target.style.transform = "translateY(-2px)";
                e.target.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
              }}
              onMouseOut={(e) => {
                e.target.style.transform = "translateY(0)";
                e.target.style.boxShadow = "none";
              }}
            >
              {b.label}
            </button>
          ))}
        </div>
      )}

      {/* Resource Builder */}
      {hint.show_resource_builder && (
        <div style={{ 
          backgroundColor: "white", 
          padding: "20px", 
          borderRadius: "8px",
          border: "1px solid #dee2e6"
        }}>
          <h4 style={{ margin: "0 0 16px 0", color: "#495057" }}>👥 Select Team Resources</h4>
          
          {/* Horizontal Layout - 3 per row */}
          <div style={{ 
            display: "grid", 
            gridTemplateColumns: "repeat(3, 1fr)", 
            gap: "12px", 
            marginBottom: "20px",
            maxWidth: "100%"
          }}>
            {hint.resource_roles?.map((role) => {
              const count = getResourceCount(role);
              return (
                <div key={role} style={{ 
                  display: "flex", 
                  flexDirection: "column",
                  alignItems: "center",
                  padding: "12px 8px",
                  backgroundColor: count > 0 ? "#e3f2fd" : "#f8f9fa",
                  borderRadius: "8px",
                  border: `2px solid ${count > 0 ? "#2196f3" : "#e9ecef"}`,
                  minHeight: "100px",
                  justifyContent: "space-between"
                }}>
                  <span style={{ 
                    fontWeight: "500", 
                    fontSize: "13px", 
                    textAlign: "center",
                    lineHeight: "1.2",
                    marginBottom: "8px"
                  }}>
                    {role}
                  </span>
                  
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <button 
                      onClick={() => onClick(`-:${role}`)}
                      disabled={count === 0}
                      style={{
                        width: "28px",
                        height: "28px",
                        borderRadius: "50%",
                        border: "none",
                        backgroundColor: count > 0 ? "#dc3545" : "#e9ecef",
                        color: "white",
                        cursor: count > 0 ? "pointer" : "not-allowed",
                        fontSize: "16px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center"
                      }}
                    >
                      −
                    </button>
                    <span style={{ 
                      minWidth: "20px", 
                      textAlign: "center", 
                      fontWeight: "bold",
                      fontSize: "16px",
                      color: count > 0 ? "#2196f3" : "#6c757d"
                    }}>
                      {count}
                    </span>
                    <button 
                      onClick={() => onClick(`+:${role}`)}
                      style={{
                        width: "28px",
                        height: "28px",
                        borderRadius: "50%",
                        border: "none",
                        backgroundColor: "#28a745",
                        color: "white",
                        cursor: "pointer",
                        fontSize: "16px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center"
                      }}
                    >
                      +
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          <button 
            onClick={() => onClick("next")}
            style={{
              padding: "12px 32px",
              backgroundColor: "#28a745",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontSize: "16px",
              fontWeight: "500",
              cursor: "pointer",
              width: "100%"
            }}
          >
            ✅ Continue to Contacts
          </button>
        </div>
      )}

      {/* Contact Dropdown */}
      {hint.contact_dropdown && (
        <div style={{ 
          backgroundColor: "white", 
          padding: "20px", 
          borderRadius: "8px",
          border: "1px solid #dee2e6"
        }}>
          <h4 style={{ margin: "0 0 16px 0", color: "#495057" }}>🏢 Select Contact</h4>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {hint.contact_dropdown.map((contact) => (
              <div 
                key={contact.id}
                onClick={() => handleContactSelect(contact)}
                style={{
                  padding: "16px",
                  border: "2px solid #e9ecef",
                  borderRadius: "8px",
                  cursor: "pointer",
                  transition: "all 0.2s",
                  backgroundColor: selectedContact?.id === contact.id ? "#e3f2fd" : "white"
                }}
                onMouseOver={(e) => {
                  if (selectedContact?.id !== contact.id) {
                    e.target.style.borderColor = "#007bff";
                    e.target.style.backgroundColor = "#f8f9fa";
                  }
                }}
                onMouseOut={(e) => {
                  if (selectedContact?.id !== contact.id) {
                    e.target.style.borderColor = "#e9ecef";
                    e.target.style.backgroundColor = "white";
                  }
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <h5 style={{ margin: "0 0 8px 0", color: "#212529", fontSize: "16px" }}>
                      {contact.details.name}
                    </h5>
                    <p style={{ margin: "0 0 4px 0", color: "#6c757d", fontSize: "14px" }}>
                      <strong>{contact.details.contact_person}</strong> - {contact.details.designation}
                    </p>
                    <p style={{ margin: "0", color: "#6c757d", fontSize: "13px" }}>
                      📧 {contact.details.email} | 📞 {contact.details.phone}
                    </p>
                  </div>
                  <span style={{
                    padding: "4px 12px",
                    backgroundColor: contact.details.type === "client" ? "#28a745" : "#007bff",
                    color: "white",
                    borderRadius: "12px",
                    fontSize: "12px",
                    fontWeight: "500"
                  }}>
                    {contact.details.type.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generate Button */}
      {hint.generate_buttons && (
        <div style={{ display: "flex", justifyContent: "center" }}>
          {hint.generate_buttons.map((b) => (
            <button 
              key={b.id} 
              onClick={() => onClick(b.value)}
              style={{
                padding: "16px 48px",
                backgroundColor: "#28a745",
                color: "white",
                border: "none",
                borderRadius: "12px",
                fontSize: "18px",
                fontWeight: "600",
                cursor: "pointer",
                boxShadow: "0 4px 12px rgba(40, 167, 69, 0.3)",
                transition: "all 0.2s"
              }}
              onMouseOver={(e) => {
                e.target.style.transform = "translateY(-2px)";
                e.target.style.boxShadow = "0 6px 20px rgba(40, 167, 69, 0.4)";
              }}
              onMouseOut={(e) => {
                e.target.style.transform = "translateY(0)";
                e.target.style.boxShadow = "0 4px 12px rgba(40, 167, 69, 0.3)";
              }}
            >
              {b.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}