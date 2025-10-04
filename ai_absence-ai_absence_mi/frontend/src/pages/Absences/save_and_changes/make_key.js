// Tiny helper for keys
export function makeKey(employeeId, isoString) {
  return `${employeeId}-${isoString}`;
}