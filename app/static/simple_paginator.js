let currentPage = 1;
const perPage = 10;
async function fetchData(page) {
	const response = await fetch(`/${data_endpoint}?page=${page}&per_page=${perPage}`);
	const result = await response.json();
	renderData(result.data);
	renderPagination(result.page, result.total_pages);
};
function renderData(data) {
	const container = document.getElementById('data-container');
	container.innerHTML = data.map(item => `<a href=${item.path}>${item.title}</a><br>`).join('');
};
function renderPagination(current, total) {
	const controls = document.getElementById('pagination-controls');
	controls.innerHTML = '';
	if (current > 1) {
		const prevButton = document.createElement('button');
		prevButton.textContent = 'Previous';
		prevButton.className = 'w3-button my-lilac w3-margin-right';
		prevButton.onclick = () => fetchData(current - 1);
		controls.appendChild(prevButton);
	}
	if (current < total) {
		const nextButton = document.createElement('button');
		nextButton.textContent = 'Next';
		nextButton.className = 'w3-button my-lilac';
		nextButton.onclick = () => fetchData(current + 1);
		controls.appendChild(nextButton);
	}
};
fetchData(currentPage);
