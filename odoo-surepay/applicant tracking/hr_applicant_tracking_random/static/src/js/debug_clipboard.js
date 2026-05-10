// Debug logging for clipboard API availability
console.log('=== Clipboard API Debug ===');
console.log('navigator.clipboard exists:', !!navigator.clipboard);
console.log('navigator.clipboard object:', navigator.clipboard);
console.log('navigator.clipboard.writeText exists:', typeof navigator.clipboard?.writeText);
console.log('navigator.clipboard.writeText function:', navigator.clipboard?.writeText);
console.log('Is secure context:', window.isSecureContext);
console.log('User agent:', navigator.userAgent);
console.log('=== End Clipboard API Debug ===');