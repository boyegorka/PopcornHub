// Функционал для выбора всех чекбоксов
document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all');
    const movieCheckboxes = document.getElementsByName('selected_movies');

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            movieCheckboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
        });
    }

    // Показывать/скрывать select для нового статуса
    const actionSelect = document.querySelector('select[name="action"]');
    const statusSelect = document.querySelector('select[name="new_status"]');

    if (actionSelect && statusSelect) {
        actionSelect.addEventListener('change', function() {
            statusSelect.style.display = 
                this.value === 'update_status' ? 'block' : 'none';
        });
    }
}); 