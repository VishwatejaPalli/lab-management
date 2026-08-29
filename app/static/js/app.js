// Lab Management System - Client JS

// Session timer
function startTimer(startTimeISO) {
    const startTime = new Date(startTimeISO);
    const timerEl = document.getElementById('session-timer');
    if (!timerEl) return;

    function update() {
        const now = new Date();
        const diff = Math.floor((now - startTime) / 1000);
        const hours = Math.floor(diff / 3600);
        const minutes = Math.floor((diff % 3600) / 60);
        const seconds = diff % 60;
        timerEl.textContent =
            String(hours).padStart(2, '0') + ':' +
            String(minutes).padStart(2, '0') + ':' +
            String(seconds).padStart(2, '0');
    }
    update();
    setInterval(update, 1000);
}

// Dynamic form: show/hide fields based on activity type
document.addEventListener('DOMContentLoaded', function () {
    const activitySelect = document.getElementById('activity_type_id');
    if (activitySelect) {
        activitySelect.addEventListener('change', function () {
            const selected = this.options[this.selectedIndex];
            const activityName = selected ? selected.text.toLowerCase() : '';

            document.querySelectorAll('.activity-field').forEach(el => {
                el.style.display = 'none';
            });

            if (activityName.includes('experiment')) {
                document.getElementById('experiment-fields').style.display = 'block';
            } else if (activityName.includes('project')) {
                document.getElementById('project-fields').style.display = 'block';
            } else if (activityName.includes('research')) {
                document.getElementById('research-fields').style.display = 'block';
            }
            // practice shows no extra fields
        });
    }

    // Filter experiments by course
    const courseSelect = document.getElementById('course_id');
    if (courseSelect) {
        courseSelect.addEventListener('change', function () {
            const courseId = this.value;
            const experimentSelect = document.getElementById('experiment_id');
            if (experimentSelect) {
                Array.from(experimentSelect.options).forEach(opt => {
                    if (opt.value === '' || opt.value === '0') {
                        opt.style.display = '';
                    } else {
                        opt.style.display = opt.dataset.courseId === courseId ? '' : 'none';
                    }
                });
                experimentSelect.value = '';
            }
        });
    }
});
