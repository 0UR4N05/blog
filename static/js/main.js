function updateCursorPosition() {
    const filePathText = document.getElementById('file-path-txt');
    const cursor = document.getElementById('cursor');
    const rect = filePathText.getBoundingClientRect();
    cursor.style.top = `${rect.top}px`;
    cursor.style.left = `${rect.right}px`;
}
async function fetchAndCopyContent(url) {
    try {
	const response = await fetch(url);
	if (!response.ok) {
	    throw new Error('Network response was not ok');
	}
	const content = await response.text();
	await navigator.clipboard.writeText(content);
	console.log('Content copied to clipboard!');
    } catch (error) {
	console.log('Failed to fetch or copy content: ' + error.message);
    }
}

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
	const filepath = document.getElementById('file-path-txt');
	filepath.textContent = path;
	if (data.type === 'directory') {
	    for (const item of data.contents) {
		const button = document.createElement('button');
		button.className =  item.type === 'dir' ? 'folder-icon' : 'file-icon'
		button.textContent = item.filename;
		const itemPath = fileExplorer.resolvePath(`${path}${item.filename}`);
		if (item.type === "file"){
		    button.onclick = async () => {
			const itemData = await fileExplorer.fetchDirectory(itemPath);
			fileExplorer.renderFile(itemPath);
			const downloadButton = document.getElementById('download-button');
			const downloadLink = document.createElement('a');
			downloadLink.href = `content${path}${item.filename}`;
			downloadLink.download = `${item.filename}`;
			downloadButton.addEventListener('click', function() {
			    downloadLink.click();
			});
			document.getElementById('copy-button').addEventListener('click', function() {
			    const url = `content${path}${item.filename}`;
			    console.log(url)
			    fetchAndCopyContent(url);
			});
		    }
		} else if (item.type === "dir") {
		    button.onclick = async () => {
			const itemData = await fileExplorer.fetchDirectory(itemPath);
			const childrenDiv = button.nextElementSibling;
			if (childrenDiv && childrenDiv.nodeName != "BUTTON") {
			    childrenDiv.style.display = childrenDiv.style.display === 'none' ? 'block' : 'none';
			} else {
			    const newChildrenDiv = document.createElement('div');
			    newChildrenDiv.className = 'children';
			    await renderFileTree(newChildrenDiv, itemPath);
			    button.parentNode.insertBefore(newChildrenDiv, button.nextSibling);
			}
		    }
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
updateCursorPosition();
window.addEventListener('resize', updateCursorPosition);
setInterval(updateCursorPosition, 50);

