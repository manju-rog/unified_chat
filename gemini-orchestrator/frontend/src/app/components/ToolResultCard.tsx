interface ToolResultCardProps {
  toolCall: {
    name: string
    args: any
  }
}

export default function ToolResultCard({ toolCall }: ToolResultCardProps) {
  const getActionDetails = () => {
    switch (toolCall.name) {
      case 'mark_absent':
        return {
          icon: '📅',
          title: 'Marked Absent',
          details: [
            { label: 'Employee', value: toolCall.args.employee_id },
            { label: 'Date', value: toolCall.args.date },
            { label: 'Reason', value: toolCall.args.reason || 'Not specified' }
          ]
        }
      case 'mark_present':
        return {
          icon: '✓',
          title: 'Marked Present',
          details: [
            { label: 'Employee', value: toolCall.args.employee_id },
            { label: 'Date', value: toolCall.args.date }
          ]
        }
      case 'get_absence_status':
        return {
          icon: '🔍',
          title: 'Checked Status',
          details: [
            { label: 'Employee', value: toolCall.args.employee_id },
            { label: 'Date', value: toolCall.args.date || 'Today' }
          ]
        }
      case 'start_sow':
        return {
          icon: '📄',
          title: 'Started SOW',
          details: [
            { label: 'Project', value: toolCall.args.project_name }
          ]
        }
      case 'update_sow':
        return {
          icon: '✏️',
          title: 'Updated SOW',
          details: [
            { label: 'SOW ID', value: toolCall.args.sow_id }
          ]
        }
      case 'generate_sow':
        return {
          icon: '📥',
          title: 'Generated SOW',
          details: [
            { label: 'SOW ID', value: toolCall.args.sow_id }
          ]
        }
      default:
        return {
          icon: '⚙️',
          title: 'Action Completed',
          details: [
            { label: 'Action', value: toolCall.name }
          ]
        }
    }
  }

  const actionDetails = getActionDetails()

  return (
    <div className="mt-3 p-4 bg-green-50 border-l-4 border-green-500 rounded-md shadow-sm">
      <div className="flex items-start">
        <span className="text-2xl mr-3">{actionDetails.icon}</span>
        <div className="flex-1">
          <h4 className="font-semibold text-green-800 mb-2">{actionDetails.title}</h4>
          <div className="space-y-1">
            {actionDetails.details.map((detail, idx) => (
              <div key={idx} className="flex text-sm">
                <span className="font-medium text-green-700 mr-2">{detail.label}:</span>
                <span className="text-green-900">{detail.value}</span>
              </div>
            ))}
          </div>
        </div>
        <span className="text-green-600 text-xl">✓</span>
      </div>
    </div>
  )
}
