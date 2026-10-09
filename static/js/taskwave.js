/* ============================================================
   TASKWAVE - Core Client-side Interactivity
   - Kanban Drag-and-Drop with Database Sync
   - Subtask AJAX Toggles
   - Notification AJAX Read
   - Mobile Sidebar Toggle
   ============================================================ */

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
  // Sidebar Toggle (Desktop Collapse & Mobile Drawer)
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.app-sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (window.innerWidth <= 992) {
        sidebar.classList.toggle('show');
        let backdrop = document.querySelector('.sidebar-backdrop');
        if (!backdrop) {
          backdrop = document.createElement('div');
          backdrop.className = 'sidebar-backdrop';
          document.body.appendChild(backdrop);
          backdrop.addEventListener('click', () => {
            sidebar.classList.remove('show');
            backdrop.classList.remove('show');
          });
        }
        backdrop.classList.toggle('show', sidebar.classList.contains('show'));
      } else {
        sidebar.classList.toggle('collapsed');
      }
    });
  }

  // Subtask Checkbox Toggles
  document.querySelectorAll('.subtask-toggle').forEach(checkbox => {
    checkbox.addEventListener('change', async (e) => {
      const subtaskId = e.target.dataset.subtaskId;
      const progressLabel = document.getElementById('taskProgressValue');
      const progressBar = document.getElementById('taskProgressBar');

      try {
        const response = await fetch(`/api/subtasks/${subtaskId}/toggle/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
          }
        });
        const data = await response.json();
        if (data.success) {
          if (progressLabel) progressLabel.innerText = `${data.progress}%`;
          if (progressBar) progressBar.style.width = `${data.progress}%`;
          const textSpan = e.target.closest('li').querySelector('.subtask-title');
          if (textSpan) {
            textSpan.classList.toggle('text-decoration-line-through', data.is_completed);
            textSpan.classList.toggle('text-muted', data.is_completed);
          }
        }
      } catch (err) {
        console.error('Error toggling subtask:', err);
      }
    });
  });

  // Kanban Drag and Drop
  const draggables = document.querySelectorAll('.kanban-card');
  const containers = document.querySelectorAll('.kanban-tasks-list');

  draggables.forEach(draggable => {
    draggable.addEventListener('dragstart', () => {
      draggable.classList.add('dragging');
    });

    draggable.addEventListener('dragend', async () => {
      draggable.classList.remove('dragging');
      const newColumn = draggable.closest('.kanban-column');
      const newStatus = newColumn.dataset.status;
      const taskId = draggable.dataset.taskId;

      if (newStatus && taskId) {
        try {
          await fetch(`/api/tasks/${taskId}/update-status/`, {
            method: 'POST',
            headers: {
              'X-CSRFToken': getCookie('csrftoken'),
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
          });
        } catch (err) {
          console.error('Failed to update task status:', err);
        }
      }
    });
  });

  containers.forEach(container => {
    container.addEventListener('dragover', (e) => {
      e.preventDefault();
      const dragging = document.querySelector('.dragging');
      if (dragging) {
        container.appendChild(dragging);
      }
    });
  });
});
