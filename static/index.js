document.addEventListener("DOMContentLoaded", function () {
    const menuCheckbox = document.getElementById('menu-checkbox');
    const sidebar = document.querySelector('.sidebar');

    menuCheckbox.addEventListener('change', function () {
        if (menuCheckbox.checked) {
            sidebar.style.width = '250px';
        } else {
            sidebar.style.width = '0';
        }
    });
});
