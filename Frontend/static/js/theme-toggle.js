// Marino RAKOTONJANAHARY - rakotonjanaharymarino@gmail.com
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const sunIcon = document.getElementById('sunIcon');
    const moonIcon = document.getElementById('moonIcon');
    const html = document.documentElement;

    function setTheme(theme) {
        html.setAttribute('data-theme', theme);
        localStorage.setItem('marihar-theme', theme);
        updateIcons(theme);
    }

    function updateIcons(theme) {
        if (theme === 'light') {
            sunIcon.style.opacity = '0';
            sunIcon.style.transform = 'scale(0.5) rotate(-90deg)';
            sunIcon.style.pointerEvents = 'none';

            moonIcon.style.opacity = '1';
            moonIcon.style.transform = 'scale(1) rotate(0deg)';
            moonIcon.style.pointerEvents = 'auto';
        } else {
            sunIcon.style.opacity = '1';
            sunIcon.style.transform = 'scale(1) rotate(0deg)';
            sunIcon.style.pointerEvents = 'auto';

            moonIcon.style.opacity = '0';
            moonIcon.style.transform = 'scale(0.5) rotate(90deg)';
            moonIcon.style.pointerEvents = 'none';
        }
    }

    function toggleTheme() {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    }

    const savedTheme = localStorage.getItem('marihar-theme');
    const initialTheme = savedTheme || 'dark';
    setTheme(initialTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleTheme();
        });
    }

    window.toggleTheme = toggleTheme;
    window.setTheme = setTheme;
    window.updateIcons = updateIcons;
});
