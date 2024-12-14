// Manejo de la subida de imágenes de perfil
document.addEventListener('DOMContentLoaded', function() {
    const profileImageContainer = document.getElementById('profileImageContainer');
    const dragOverlay = document.getElementById('dragOverlay');
    const profileImageInput = document.getElementById('profileImageInput');

    // Prevenir comportamiento por defecto del navegador
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        profileImageContainer.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Manejo de eventos de arrastrar
    ['dragenter', 'dragover'].forEach(eventName => {
        profileImageContainer.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        profileImageContainer.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dragOverlay.classList.remove('d-none');
    }

    function unhighlight(e) {
        dragOverlay.classList.add('d-none');
    }

    // Manejo de soltar archivo
    profileImageContainer.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        handleFiles(files);
    }

    // Manejo de selección de archivo mediante el input
    profileImageInput.addEventListener('change', function(e) {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                uploadFile(file);
            } else {
                alert('Por favor, sube solo imágenes.');
            }
        }
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('profile_image', file);

        fetch('/user/upload-profile-image', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar la imagen en el contenedor
                const img = document.createElement('img');
                img.src = data.image_url;
                img.classList.add('w-100', 'h-100', 'object-fit-cover');
                
                const container = document.getElementById('profileImageContainer');
                container.innerHTML = '';
                container.appendChild(img);
            } else {
                alert('Error al subir la imagen: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al subir la imagen');
        });
    }
});
