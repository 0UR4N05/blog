function updateCursorPosition() {
    const filePathText = document.getElementById('file-path-txt');
    const cursor = document.getElementById('cursor');
    const rect = filePathText.getBoundingClientRect();
    cursor.style.top = `${rect.top}px`;
    cursor.style.left = `${rect.right}px`;
}
async function fetchAndCopyContent(url) {
    try {
	const response = await fetch(`${window.location.protocol}//${window.location.host}/${url}`);
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

function setDownloadLink(dir, filename){
	const downloadButton = document.getElementById('download-button');
	const downloadLink = document.createElement('a');
	downloadButton.addEventListener('click', function() {
	    downloadLink.click();
	});
	downloadLink.href = `${window.location.protocol}//${window.location.host}/${dir}`;
	downloadLink.download = filename;
}

async function renderFileTree(container, path = '/') {
	container.innerHTML = '';
	const data = await fileExplorer.fetchDirectory(path);
	const filepath = document.getElementById('file-path-txt');
	const cdirpath = fileExplorer.resolvePath(`${window.location.pathname}`);
	const cdir = await fileExplorer.fetchDirectory(cdirpath);

	if (data.type === 'directory') {
	    for (const item of data.contents) {
		const button = document.createElement('button');
		button.className =  item.type === 'dir' ? 'folder-icon' : 'file-icon'
		button.textContent = item.filename;
		const itemPath = fileExplorer.resolvePath(`${path}${item.filename}`);
		if (item.filename == "README.md" && cdir.type === "directory"){
		    await fileExplorer.renderFile(itemPath);
		}
		if (item.type === "file"){
		    button.onclick = async () => {
			document.getElementById('copy-button').addEventListener('click', function() {
			    const url = `content${path}${item.filename}`;
			    fetchAndCopyContent(url);
			});
			const itemData = await fileExplorer.fetchDirectory(itemPath);
			fileExplorer.renderFile(itemPath);
			setDownloadLink(`content${path}${item.filename}`, item.filename);
			filepath.textContent = `${path}${item.filename}`;
			history.pushState({}, "", `${path}${item.filename}`)
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
			filepath.textContent = itemPath;
			history.pushState({}, "", itemPath)
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

async function main() {
    if (window.location.pathname != "/"){
	const itemPath = fileExplorer.resolvePath(`${window.location.pathname}`);
	const filepath = document.getElementById('file-path-txt');
	filepath.textContent = `${window.location.pathname}`;
	const data = await fileExplorer.fetchDirectory(itemPath);
	console.log(data)
	if (data.type  === 'directory'){
	    renderFileTree(document.getElementById('fileTree'), window.location.pathname);
	} else {
	    await fileExplorer.renderFile(itemPath);
	    renderFileTree(document.getElementById('fileTree'));
	    setDownloadLink(`content${itemPath}`, data.filename);
	    document.getElementById('copy-button').addEventListener('click', function() {
		const url = `content${itemPath}`;
		fetchAndCopyContent(url);
	    });
	}
    } else {
	renderFileTree(document.getElementById('fileTree'));
    }
}

main()
updateCursorPosition();
window.addEventListener('resize', updateCursorPosition);
setInterval(updateCursorPosition, 50);

