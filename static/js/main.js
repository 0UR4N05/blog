const fileExplorer = {
    currentPath: '/',
    fileContent: document.getElementById('fileContent'),

    async fetchDirectory(path) {
	try {
	    const response = await fetch(`/ls?path=${encodeURIComponent(path)}`);
	    return await response.json();
	} catch (error) {
	    console.error('Error fetching directory:', error);
	    return { type: 'error', message: error.message };
	}
    },

    async fetchFile(path) {
	try {
	    const response = await fetch(`/ls?path=${encodeURIComponent(path)}`);
	    return await response.json();
	} catch (error) {
	    console.error('Error fetching file:', error);
	    return { type: 'error', message: error.message };
	}
    },

    async renderFile(path) {
	const data = await this.fetchFile(path);
	if (data.type === 'file') {
	    this.fileContent.innerHTML = data.contents;
	} else {
	    this.fileContent.textContent = `Error: ${data.message || 'Unable to render file'}`;
	}
    },

    resolvePath(path) {
	if (path.startsWith('/')) {
	    return path;
	}
	return `${this.currentPath}/${path}`.replace(/\/+/g, '/');
    }
};

async function renderFileTree(container, path = '/') {
    container.innerHTML = '';
    const data = await fileExplorer.fetchDirectory(path);
    if (data.type === 'directory') {
	for (const item of data.contents) {
	    const button = document.createElement('button');
	    const itemPath = fileExplorer.resolvePath(`${path}${item}`);
	    const itemData = await fileExplorer.fetchDirectory(itemPath);
	    
	    button.className = itemData.type === 'directory' ? 'folder-icon' : 'file-icon';
	    button.textContent = item;

	    if (itemData.type === 'file') {
		button.onclick = () => fileExplorer.renderFile(itemPath);
	    } else if (itemData.type === 'directory') {
		button.onclick = async () => {
		    const childrenDiv = button.nextElementSibling;
		    if (childrenDiv && childrenDiv.nodeName != "BUTTON") {
			childrenDiv.style.display = childrenDiv.style.display === 'none' ? 'block' : 'none';
		    } else {
			const newChildrenDiv = document.createElement('div');
			newChildrenDiv.className = 'children';
			await renderFileTree(newChildrenDiv, itemPath);
			button.parentNode.insertBefore(newChildrenDiv, button.nextSibling);
		    }
		};
	    }

	    container.appendChild(button);
	}
    } else {
	const errorMsg = document.createElement('div');
	errorMsg.textContent = `Error: ${data.message || 'Unable to load directory'}`;
	container.appendChild(errorMsg);
    }
}

renderFileTree(document.getElementById('fileTree'));

