// Minimal test component
console.log('Test script loaded successfully');

(function() {
    function defineComponent() {
        if (typeof React === 'undefined') {
            console.log('React not available, retrying...');
            setTimeout(defineComponent, 100);
            return;
        }
        
        console.log('React available, defining test component');
        
        function TestComponent() {
            return React.createElement('div', { className: 'alert alert-success' }, 
                'Test component working!'
            );
        }
        
        window.TestComponent = TestComponent;
        console.log('Test component exported to window');
    }
    
    defineComponent();
})();
