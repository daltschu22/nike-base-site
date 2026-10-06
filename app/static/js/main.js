/**
 * Nike Missile Base Map - Main JavaScript
 * Common functionality used across the application
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add active state to current nav item
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        if (new URL(link.href, window.location.origin).pathname === currentLocation) {
            link.classList.add('bg-white/15', 'text-white');
            link.setAttribute('aria-current', 'page');
        }
    });

    // Auto-dismiss flash messages if present
    const flashMessages = document.querySelectorAll('[data-flash]');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.classList.add('opacity-0');
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});
