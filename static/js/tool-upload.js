/**
 * tool-upload.js — Shared Upload Component for iLovePDF tools
 *
 * Features:
 *  - Thumbnail preview (images show preview, PDFs show icon + name)
 *  - File size display beneath thumbnail
 *  - 30 MB total size limit with warning
 *  - Add more files button
 *  - Remove individual files
 *  - Drag & drop reorder
 *
 * Usage:
 *   const uploader = new ToolUpload({
 *     dropZone: '#uploadBox',
 *     fileInput: '#fileInput',
 *     previewContainer: '#filePreview',
 *     fileListInput: '#fileListData',  // hidden input or direct form
 *     maxSizeMB: 30,
 *     accept: '.pdf',
 *     multiple: true,
 *     onFilesChange: function(files) { ... }
 *   });
 */

// PEP 8 equivalent: consistent naming, well-documented
/* global DataTransfer */

class ToolUpload {
    /**
     * Initialize the upload component.
     * @param {Object} config - Configuration options.
     */
    constructor(config) {
        this.config = Object.assign({
            dropZone: '#uploadBox',
            fileInput: '#fileInput',
            previewContainer: '#filePreview',
            warningContainer: '#sizeWarning',
            maxSizeMB: 30,
            accept: '.pdf',
            multiple: true,
            onFilesChange: null,
        }, config);

        // Maximum size in bytes
        this.maxSizeBytes = this.config.maxSizeMB * 1024 * 1024;

        // Internal file list (maintains order)
        this.files = [];

        // Drag state
        this.dragSrcIndex = null;

        this._init();
    }

    /**
     * Set up event listeners for drop zone, file input, and drag events.
     */
    _init() {
        this.dropZone = document.querySelector(this.config.dropZone);
        this.fileInput = document.querySelector(this.config.fileInput);
        this.previewContainer = document.querySelector(
            this.config.previewContainer
        );
        this.warningContainer = document.querySelector(
            this.config.warningContainer
        );

        if (!this.dropZone || !this.fileInput || !this.previewContainer) {
            console.warn('ToolUpload: Missing required DOM elements.');
            return;
        }

        // File input change
        this.fileInput.addEventListener('change', (e) => {
            this._addFiles(Array.from(e.target.files));
        });

        // Drag-and-drop onto upload zone
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('drag-over');
        });
        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('drag-over');
        });
        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                this._addFiles(Array.from(e.dataTransfer.files));
            }
        });
    }

    /**
     * Add files to the internal list, validate size, and render.
     * @param {File[]} newFiles - Array of File objects to add.
     */
    _addFiles(newFiles) {
        // Filter by accept type if specified
        const accept = this.config.accept;
        if (accept) {
            const exts = accept.split(',').map(
                (s) => s.trim().toLowerCase()
            );
            newFiles = newFiles.filter((f) => {
                const name = f.name.toLowerCase();
                return exts.some(
                    (ext) => name.endsWith(ext) ||
                        f.type.includes(ext.replace('.', ''))
                );
            });
        }

        this.files = this.files.concat(newFiles);
        this._syncFileInput();
        this._render();
        this._checkSize();
        this._notifyChange();
    }

    /**
     * Remove a file by index from the internal list.
     * @param {number} index - Index of the file to remove.
     */
    removeFile(index) {
        this.files.splice(index, 1);
        this._syncFileInput();
        this._render();
        this._checkSize();
        this._notifyChange();
    }

    /**
     * Sync internal file list back to the native file input using
     * DataTransfer (allows form submission with correct files).
     */
    _syncFileInput() {
        const dt = new DataTransfer();
        this.files.forEach((f) => dt.items.add(f));
        this.fileInput.files = dt.files;
    }

    /**
     * Check total size and show/hide warning.
     */
    _checkSize() {
        const totalSize = this.files.reduce(
            (sum, f) => sum + f.size, 0
        );
        if (this.warningContainer) {
            if (totalSize > this.maxSizeBytes) {
                this.warningContainer.style.display = 'block';
                this.warningContainer.innerHTML =
                    `<svg xmlns="http://www.w3.org/2000/svg" width="20" ` +
                    `height="20" fill="none" stroke="currentColor" ` +
                    `stroke-width="2" class="me-2" viewBox="0 0 24 24">` +
                    `<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h` +
                    `16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-` +
                    `3.42 0z"></path><line x1="12" y1="9" x2="12" ` +
                    `y2="13"></line><line x1="12" y1="17" x2="12.01"` +
                    ` y2="17"></line></svg>` +
                    `Total file size (${this._formatSize(totalSize)})` +
                    ` exceeds the ${this.config.maxSizeMB} MB limit. ` +
                    `Please remove some files.`;
            } else {
                this.warningContainer.style.display = 'none';
            }
        }
    }

    /**
     * Notify external callback of file list changes.
     */
    _notifyChange() {
        if (typeof this.config.onFilesChange === 'function') {
            this.config.onFilesChange(this.files);
        }
    }

    /**
     * Render file thumbnails with drag-reorder, remove buttons.
     */
    _render() {
        this.previewContainer.innerHTML = '';

        if (this.files.length === 0) {
            this.previewContainer.style.display = 'none';
            return;
        }

        this.previewContainer.style.display = 'grid';

        this.files.forEach((file, index) => {
            const card = document.createElement('div');
            card.className = 'file-thumbnail-card';
            card.draggable = true;
            card.dataset.index = index;

            // Drag events for reorder
            card.addEventListener('dragstart', (e) => {
                this.dragSrcIndex = index;
                card.classList.add('drag-ghost');
                e.dataTransfer.effectAllowed = 'move';
            });
            card.addEventListener('dragend', () => {
                card.classList.remove('drag-ghost');
                // Remove drag-over from all cards
                this.previewContainer.querySelectorAll(
                    '.file-thumbnail-card'
                ).forEach((c) => c.classList.remove('drag-over-card'));
            });
            card.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                card.classList.add('drag-over-card');
            });
            card.addEventListener('dragleave', () => {
                card.classList.remove('drag-over-card');
            });
            card.addEventListener('drop', (e) => {
                e.preventDefault();
                card.classList.remove('drag-over-card');
                const targetIndex = index;
                if (
                    this.dragSrcIndex !== null &&
                    this.dragSrcIndex !== targetIndex
                ) {
                    // Swap files
                    const movedFile = this.files.splice(
                        this.dragSrcIndex, 1
                    )[0];
                    this.files.splice(targetIndex, 0, movedFile);
                    this._syncFileInput();
                    this._render();
                    this._notifyChange();
                }
                this.dragSrcIndex = null;
            });

            // Thumbnail preview area
            const thumbArea = document.createElement('div');
            thumbArea.className = 'file-thumb-area';

            if (file.type.startsWith('image/')) {
                // Image preview
                const img = document.createElement('img');
                img.className = 'file-thumb-img';
                img.alt = file.name;
                const reader = new FileReader();
                reader.onload = (e) => {
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
                thumbArea.appendChild(img);
            } else {
                // File icon for non-image files (PDFs, docs, etc.)
                const icon = document.createElement('div');
                icon.className = 'file-thumb-icon';
                // Determine icon by extension
                const ext = file.name.split('.').pop().toUpperCase();
                icon.innerHTML =
                    `<svg xmlns="http://www.w3.org/2000/svg" width="40"` +
                    ` height="40" fill="none" stroke="currentColor" ` +
                    `stroke-width="1.5" viewBox="0 0 24 24">` +
                    `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 ` +
                    `2 2h12a2 2 0 0 0 2-2V8z"></path>` +
                    `<polyline points="14 2 14 8 20 8"></polyline>` +
                    `</svg>` +
                    `<span class="file-ext-badge">${ext}</span>`;
                thumbArea.appendChild(icon);
            }

            // Remove button
            const removeBtn = document.createElement('button');
            removeBtn.className = 'file-remove-btn';
            removeBtn.type = 'button';
            removeBtn.innerHTML = '&times;';
            removeBtn.title = 'Remove file';
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeFile(index);
            });
            thumbArea.appendChild(removeBtn);

            // Drag handle indicator
            const dragHandle = document.createElement('div');
            dragHandle.className = 'file-drag-handle';
            dragHandle.innerHTML = '⠿';
            dragHandle.title = 'Drag to reorder';
            thumbArea.appendChild(dragHandle);

            card.appendChild(thumbArea);

            // File info (name + size)
            const info = document.createElement('div');
            info.className = 'file-thumb-info';
            info.innerHTML =
                `<span class="file-thumb-name" title="${file.name}">` +
                `${this._truncateName(file.name, 18)}</span>` +
                `<span class="file-thumb-size">` +
                `${this._formatSize(file.size)}</span>`;
            card.appendChild(info);

            this.previewContainer.appendChild(card);
        });

        // Add "Add More" button
        const addMoreCard = document.createElement('div');
        addMoreCard.className = 'file-thumbnail-card file-add-card';
        addMoreCard.innerHTML =
            `<div class="file-thumb-area file-add-area">` +
            `<svg xmlns="http://www.w3.org/2000/svg" width="36" ` +
            `height="36" fill="none" stroke="currentColor" ` +
            `stroke-width="2" viewBox="0 0 24 24">` +
            `<line x1="12" y1="5" x2="12" y2="19"></line>` +
            `<line x1="5" y1="12" x2="19" y2="12"></line>` +
            `</svg>` +
            `</div>` +
            `<div class="file-thumb-info">` +
            `<span class="file-thumb-name">Add More</span>` +
            `</div>`;
        addMoreCard.addEventListener('click', () => {
            // Create a temporary file input to pick more files
            const tempInput = document.createElement('input');
            tempInput.type = 'file';
            tempInput.accept = this.config.accept;
            tempInput.multiple = this.config.multiple;
            tempInput.addEventListener('change', (e) => {
                this._addFiles(Array.from(e.target.files));
            });
            tempInput.click();
        });
        this.previewContainer.appendChild(addMoreCard);
    }

    /**
     * Format bytes to human-readable string.
     * @param {number} bytes - File size in bytes.
     * @returns {string} Formatted size string.
     */
    _formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat(
            (bytes / Math.pow(k, i)).toFixed(1)
        ) + ' ' + sizes[i];
    }

    /**
     * Truncate filename for display.
     * @param {string} name - Original filename.
     * @param {number} maxLen - Maximum display length.
     * @returns {string} Truncated name.
     */
    _truncateName(name, maxLen) {
        if (name.length <= maxLen) return name;
        const ext = name.split('.').pop();
        const base = name.substring(
            0, maxLen - ext.length - 4
        );
        return base + '...' + ext;
    }

    /**
     * Get current file list (in order).
     * @returns {File[]} Ordered file list.
     */
    getFiles() {
        return this.files;
    }

    /**
     * Get total size of all files.
     * @returns {number} Total size in bytes.
     */
    getTotalSize() {
        return this.files.reduce((sum, f) => sum + f.size, 0);
    }

    /**
     * Check if total size is within limit.
     * @returns {boolean} True if within 30 MB limit.
     */
    isWithinLimit() {
        return this.getTotalSize() <= this.maxSizeBytes;
    }
}
