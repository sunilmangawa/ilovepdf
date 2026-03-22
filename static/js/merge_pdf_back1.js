document.getElementById('upload-btn').addEventListener('click', function() {
    var filesInput = document.getElementById('pdf-files');
    var files = filesInput.files;
    var formData = new FormData();
    
    for (var i = 0; i < files.length; i++) {
        formData.append('pdf_files', files[i]);
    }
    
    fetch('/tools/merge-pdf/', { // Adjust the URL based on your configuration
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'), // Ensure CSRF token is included
        },
    })
    .then(response => response.json())
    .then(data => {
        displayFilesList(data.files);
    })
    .catch(error => console.error('Error:', error));
});

function displayFilesList(files) {
    const filesList = document.getElementById('files-list');
    filesList.innerHTML = ''; // Clear existing items
    files.forEach((file, index) => {
        const listItem = document.createElement('li');
        listItem.setAttribute('data-id', file.id); // Assuming each file has a unique ID
        listItem.textContent = file.name;
        filesList.appendChild(listItem);
    });
    
    // Show merge button
    document.getElementById('merge-btn').style.display = 'block';
    
    // Initialize drag-and-drop functionality here
}

// Helper to get CSRF token
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

// Add event listener for the merge button
document.getElementById('merge-btn').addEventListener('click', function() {
    const filesList = document.getElementById('files-list');
    const orderedIds = Array.from(filesList.children).map(item => item.getAttribute('data-id'));
    
    fetch('/tools/merge/', { // Adjust the URL for the merge operation
        method: 'POST',
        body: JSON.stringify({ 'ordered_ids': orderedIds }),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'merged.pdf';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => console.error('Error:', error));
});
