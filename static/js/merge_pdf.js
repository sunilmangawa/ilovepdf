// merge_pdf.js
document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.querySelector('.drop-area');

    // Handle multiple file uploads
    function handleFiles(files) {
        for (let i = 0; i < files.length; i++) {
            let file = files[i];
            if (!file.type.match('application/pdf')) continue;

            createThumbnail(file);
        }
    }

    // Display thumbnails in the list
    function createThumbnail(file) {
        const li = document.createElement('li');
        li.className = 'thumbnail';
        li.draggable = true;
        li.textContent = file.name;

        // Create a container for the thumbnail image (placeholder for now)
        const imgContainer = document.createElement('div');
        imgContainer.className = 'img-container';

        // Show placeholder image
        const imgPlaceholder = document.createElement('img');
        imgPlaceholder.src = "{% static 'images/pdf-icon.png' %}";
        imgPlaceholder.alt = file.name;
        imgPlaceholder.width = 64;

        imgContainer.appendChild(imgPlaceholder);
        li.appendChild(imgContainer);

        // Allow drag and drop reordering
        li.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData("text/plain", this.textContent);
            e.target.classList.add('dragging');
        });

        li.addEventListener('dragend', function() {
            this.classList.remove('dragging');
        });

        document.getElementById('fileList').appendChild(li);

        // Clean up files on session end
        window.addEventListener('beforeunload', () => {
            sessionStorage.clear();
            localStorage.removeItem('pdf_files');
        });
    }

    dropArea.ondrop = handleFiles;
});